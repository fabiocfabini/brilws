import sys,logging
import docopt
import schema
import brilws
import prettytable
from brilws import api,params,clicommonargs
import re,time
from datetime import datetime
log = logging.getLogger('brilcalc')
logformatter = logging.Formatter('%(levelname)s %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
#fh = logging.FileHandler('/tmp/brilcalc.log')
ch.setFormatter(logformatter)
#fh.setFormatter(logformatter)
log.addHandler(ch)
#log.addHandler(fh)

def brilcalc_main():
    docstr='''

    usage:
      brilcalc (-h|--help) 
      brilcalc --version
      brilcalc --checkforupdate
      brilcalc [--debug|--nowarning] <command> [<args>...]

    commands:
      lumi Luminosity
      beam Beam       
      trg  L1 trigger
      hlt  HLT
      bkg  Background
      
    See 'brilcalc <command> --help' for more information on a specific command.

    '''
    args = {}
    argv = sys.argv[1:]
    args = docopt.docopt(docstr,argv,help=True,version=brilws.__version__,options_first=True)
    
    if '--debug' in sys.argv:
       log.setLevel(logging.DEBUG)
       ch.setLevel(logging.DEBUG)
    if args['--version'] : print brilws.__version__
    log.debug('global arguments: %s',args)
    cmmdargv = [args['<command>']] + args['<args>']

    log.debug('command arguments: %s',cmmdargv)
    parseresult = {}

    try:
      if args['<command>'] == 'lumi':
          import brilcalc_lumi

          parseresult = docopt.docopt(brilcalc_lumi.__doc__,argv=cmmdargv)
          parseresult = brilcalc_lumi.validate(parseresult)
          lumiargs = clicommonargs.parser(parseresult)
          
      elif args['<command>'] == 'beam':
          import brilcalc_beam
          import csv
          from sqlalchemy import *

          parseresult = docopt.docopt(brilcalc_beam.__doc__,argv=cmmdargv)
          parseresult = brilcalc_beam.validate(parseresult)
          beamargs = clicommonargs.parser(parseresult)

          ##db params
          dbengine = create_engine(beamargs.dbconnect)
          authpath = beamargs.authpath
          
          ##selection params
          s_bstatus = beamargs.beamstatus
          s_egev = beamargs.egev
          s_amodetag = beamargs.amodetag
          s_datatagname = beamargs.datatagname
          s_fillmin = beamargs.fillmin
          s_fillmax = beamargs.fillmax          
          s_runmin = beamargs.runmin
          s_runmax = beamargs.runmax
          s_runlsSeries = beamargs.runlsSeries                  
          s_tssecmin = beamargs.tssecmin
          s_tssecmax = beamargs.tssecmax

          ##display params
          csize = beamargs.chunksize
          withBX = beamargs.withBX
          bxcsize = csize
          totable = beamargs.totable
          fh = None
          ptable = None
          csvwriter = None

          header = ['fill','run','ls','time','beamstatus','amodetag','beamegev','intensity1','intensity2']
          if withBX:
              header = ['fill','run','ls','time','bx','bxintensity1','bxintensity2','iscolliding']
              bxcsize = csize*3564

          if not totable:
              fh = beamargs.ofilehandle
              print >> fh, '#'+','.join(header)
              csvwriter = csv.writer(fh)

          datatagname = s_datatagname
          datatagnameid = 0
          if not s_datatagname:
              r = api.max_datatagname(dbengine)
              if not r:
                  raise 'no tag found'
              datatagname = r[0]
              datatagnameid = r[1]
          else:
              datatagnameid = api.datatagnameid(dbengine,datatagname=s_datatagname)
          print 'data tag : ',datatagname
          
          nchunk = 0
          it = api.datatagIter(dbengine,datatagnameid,fillmin=s_fillmin,fillmax=s_fillmax,runmin=s_runmin,runmax=s_runmax,amodetag=s_amodetag,targetegev=s_egev,beamstatus=s_bstatus,tssecmin=s_tssecmin,tssecmax=s_tssecmax,runlsselect=s_runlsSeries ,chunksize=csize)

          if not it: exit(1)
          for idchunk in it:              
              dataids = idchunk.index              
              for beaminfochunk in api.beamInfoIter(dbengine,dataids.min(),dataids.max(),chunksize=bxcsize,withBX=withBX):
                  finalchunk = idchunk.join(beaminfochunk,how='inner',on=None,lsuffix='l',rsuffix='r',sort=False)
                  if totable:
                      ptable = prettytable.PrettyTable(header)
                      if not nchunk:
                          ptable.header = True
                      else:
                          ptable.header = False
                      ptable.align = 'l'
                      ptable.max_width['params']=80 
                  for datatagid,row in finalchunk.iterrows():
                      timestampsec = row['timestampsec']
                      dtime = datetime.fromtimestamp(int(timestampsec)).strftime(params._datetimefm)
                      if fh:
                          if not withBX:
                              csvwriter.writerow([row['fillnum'],row['runnum'],row['lsnum'],dtime,row['beamstatus'],row['amodetag'],'%.2f'%(row['egev']),'%.6e'%(row['intensity1']),'%.6e'%(row['intensity2'])])
                          else:
                              csvwriter.writerow([ row['fillnum'],row['runnum'],row['lsnum'],dtime,row['bxidx'],'%.6e'%(row['bxintensity1']),'%.6e'%(row['bxintensity2']),row['iscolliding'] ])
                      else:
                          if not withBX:
                              ptable.add_row([row['fillnum'],row['runnum'],row['lsnum'],dtime,row['beamstatus'],row['amodetag'],'%.2f'%(row['egev']),'%.6e'%(row['intensity1']),'%.6e'%(row['intensity2'])])
                          else:
                              ptable.add_row([row['fillnum'],row['runnum'],row['lsnum'],dtime,row['bxidx'],'%.6e'%(row['bxintensity1']),'%.6e'%(row['bxintensity2']),row['iscolliding'] ])

                  if beamargs.outputstyle=='tab':
                      print(ptable)
                      del ptable
                  elif beamargs.outputstyle=='html' :
                      print(ptable.get_html_string())
                      del ptable
                  del finalchunk  
                  nchunk = nchunk + 1                  
                  del beaminfochunk
              del idchunk
          if fh and fh is not sys.stdout: fh.close()  
        
      elif args['<command>'] == 'trg':
          import brilcalc_trg
          parseresult = docopt.docopt(brilcalc_trg.__doc__,argv=cmmdargv)
          parseresult = brilcalc_trg.validate(parseresult)
          
      elif args['<command>'] == 'hlt':
          import brilcalc_hlt
          parseresult = docopt.docopt(brilcalc_hlt.__doc__,argv=cmmdargv)
          parseresult = brilcalc_hlt.validate(parseresult)

      elif args['<command>'] == 'bkg':
          exit("bkg is not implemented")
      else:
          exit("%r is not a brilcalc command. See 'brilcalc --help'."%args['<command>'])
    except docopt.DocoptExit:
      raise docopt.DocoptExit('Error: incorrect input format for '+args['<command>'])            
    except schema.SchemaError as e:
      exit(e)

    if not parseresult['--debug'] :
       if parseresult['--nowarning']:
          log.setLevel(logging.ERROR)
          ch.setLevel(logging.ERROR)
    else:
       log.setLevel(logging.DEBUG)
       ch.setLevel(logging.DEBUG)
       log.debug('create arguments: %s',parseresult)

if __name__ == '__main__':
    brilcalc_main()
