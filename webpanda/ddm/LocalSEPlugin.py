import os
import shutil
from common.NrckiLogger import NrckiLogger

_logger = NrckiLogger().getLogger("DDM")

class LocalSEPlugin():
    def __init__(self, params={}):
        pass

    def get(self, src, dest):
        _logger.debug('LOCAL: Try to get file from %s to %s' % (src, dest))
        try:
            if not os.path.isfile(src):
                _logger.error("%s: File not found" % src)

            shutil.copy2(src, dest)
        except:
            _logger.error('Unable to move:%s %s' % (src, dest))


    def put(self, src, dest):
        _logger.debug('LOCAL: Try to put file from %s to %s' % (src, dest))
        if not os.path.isfile(src):
            _logger.error("%s: File not found" % src)

        self.get(src, dest)
        shutil.rmtree(os.path.join(src.split('/')[:-1]))