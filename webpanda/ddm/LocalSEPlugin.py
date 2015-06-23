import os
import shutil
import subprocess
from common import client_config
from common.NrckiLogger import NrckiLogger

_logger = NrckiLogger().getLogger("DDM")

class LocalSEPlugin():
    def __init__(self, params={}):
        self.datadir = client_config.DATA_PATH

    def get(self, src, dest):
        dest = self.datadir + dest
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

    def link(self, lfn, dir):
        lfn = self.datadir + lfn
        dir = self.datadir + dir
        _logger.debug('LOCAL: Try to link file from %s to %s' % (lfn, dir))
        try:
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out = proc.communicate("mkdir -p %s && ln -s %s %s" % (self.datadir + dir, self.datadir + lfn, self.datadir + dir))

        except:
            _logger.error('Unable to link:%s to %s' % (lfn, dir))
