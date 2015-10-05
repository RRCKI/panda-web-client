import os
import sys
import re

from configobj import ConfigObj

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
tmpConf = ConfigObj(os.path.join(basedir, 'config', 'webpanda.cfg'))

# expand all values
tmpSelf = sys.modules[ __name__ ]

for tmpKey,tmpVal in tmpConf.iteritems():
    # convert string to bool/int
    if tmpVal == 'True':
        tmpVal = True
    elif tmpVal == 'False':
        tmpVal = False
    elif re.match('^\d+$',tmpVal):
        tmpVal = int(tmpVal)
    # update dict
    tmpSelf.__dict__[tmpKey] = tmpVal

# set hostname
if not tmpSelf.__dict__.has_key('BASE_DIR'):
    tmpSelf.__dict__['BASE_DIR'] = basedir
