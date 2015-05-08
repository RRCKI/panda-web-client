import os
from configobj import ConfigObj

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
config = ConfigObj(os.path.join(basedir, 'config', 'config.ini'))