### Install

#### into brilconda virtual environment
pip install brilws
pip uninstall brilws

#### into local user area
export PYTHONPATH=$HOME/.local:$PYTHONPATH
pip install --install-option="--prefix=$HOME/.local" brilws
pip uninstall brilws

### Examples

### Build & Distribute
python setup.py sdist 
python setup.py register -r pypi
python setup.py sdist upload -r pypi
 
