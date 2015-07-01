import os
import shutil
import subprocess
from common.NrckiLogger import NrckiLogger
from ddm.DDM import ddm_getlocalabspath

_logger = NrckiLogger().getLogger("DDM")

class LocalSEPlugin():
    def __init__(self, params={}):
        self.params = params

    def get(self, src, dest):
        dest = ddm_getlocalabspath(dest)
        src = ddm_getlocalabspath(src)
        _logger.debug('LOCAL: Try to copy file from %s to %s' % (src, dest))
        try:
            if not os.path.isfile(src):
                _logger.error("%s: File not found" % src)

            shutil.copy2(src, dest)
        except:
            _logger.error('Unable to copy:%s %s' % (src, dest))


    def put(self, src, dest):
        self.get(src, dest)

    def link(self, lfn, dir):
        lfn = ddm_getlocalabspath(lfn)
        dir = ddm_getlocalabspath(dir)
        _logger.debug('LOCAL: Try to link file from %s to %s' % (lfn, dir))
        try:
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out = proc.communicate("mkdir -p %s && ln -s %s %s" % (dir, lfn, dir))

        except:
            _logger.error('Unable to link:%s to %s' % (lfn, dir))
