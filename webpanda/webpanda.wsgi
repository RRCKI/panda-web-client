import os
basedir = '/path/to/project'

activate_this = os.path.join(basedir, 'venv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, os.path.join(basedir, 'webpanda'))

from app import app as application

if __name__ == "__main__":
    application.run()