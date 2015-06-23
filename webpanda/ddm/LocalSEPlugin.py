import os
import shutil
from common import client_config
from common.NrckiLogger import NrckiLogger

_logger = NrckiLogger().getLogger("DDM")

class LocalSEPlugin():
    def __init__(self, params={}):
        self.datadir = client_config.DATA_PATH

    def get(self, src, dest):
        dest = self.datadir + dest + '/' + self.scope + '/' + self.lfn
        src = self.datadir + src
        _logger.debug('LOCAL: Try to copy file from %s to %s' % (src, dest))
        try:
            if not os.path.isfile(src):
                _logger.error("%s: File not found" % src)

            shutil.copy2(src, dest)
        except:
            _logger.error('Unable to move:%s %s' % (src, dest))


    def put(self, src, dest):
        if not os.path.isfile(src):
            _logger.error("%s: File not found" % src)

        self.get(src, dest)
