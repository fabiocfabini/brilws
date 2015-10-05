"""Usage: brilcalc trg [options] 

options:
  -h,  --help                  Show this screen.
  -c CONNECT                   DB Service name [default: offline]
  -p AUTHPATH                  Authentication file
  -r RUN                       Run number
  -o OUTPUTFILE                Output csv file. Special file '-' for stdout.
  --name NAME                  hltconfig id, key/pattern or hltpath name/pattern
  --hltconfig                  Show HLT configurations
  --prescale                   Show trigger prescale
  --ignore-mask                Ignore trigger bit masks
  --output-style OSTYLE        Screen output style. tab, html, csv [default: tab]
 
"""

import os
from docopt import docopt
from schema import Schema
from brilws.cli import clicommonargs

def validate(optdict):
    result={}
    argdict = clicommonargs.argvalidators
    #extract sub argdict here
    myvalidables = ['-c','-r','--name',str]
    argdict = dict((k,v) for k,v in clicommonargs.argvalidators.iteritems() if k in myvalidables)
    schema = Schema(argdict)
    result = schema.validate(optdict)
    return result

if __name__ == '__main__':
    print(docopt(__doc__))
