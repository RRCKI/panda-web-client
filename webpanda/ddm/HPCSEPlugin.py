import subprocess
from common.NrckiLogger import NrckiLogger
from common import client_config
from ddm.DDM import SEPlugin, ddm_getlocalabspath

_logger = NrckiLogger().getLogger("DDM")

class HPCSEPlugin(SEPlugin):
    def __init__(self, params={}):
        self.key = client_config.HPC_KEY
        self.host = client_config.HPC_HOST
        self.user = client_config.HPC_USER
        self.datadir = client_config.HPC_DATADIR
        self.params = params

    def get(self, src, dest):
        src = self.datadir + src
        dest = ddm_getlocalabspath(dest)
        _logger.debug('HPC: Try to get file from %s to %s' % (src, dest))
        try:
            if not src.startswith('/'):
                src = '/' + src
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out = proc.communicate("rsync -av -e 'ssh -i %s' %s@%s:%s %s/" % (self.key, self.user, self.host, src, dest))

        except:
            _logger.error('Unable to download:%s to %s' % (src, dest))


    def put(self, src, dest):
        src = ddm_getlocalabspath(src)
        dest = self.datadir + dest
        _logger.debug('HPC: Try to put file from %s to %s' % (src, dest))
        try:
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out = proc.communicate("ssh -i %s %s@%s 'mkdir -p %s'" % (self.key, self.user, self.host, dest))
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out = proc.communicate("rsync -av -e 'ssh -i %s' %s %s@%s:%s/" % (self.key, src, self.user, self.host, dest))

        except:
            _logger.error('Unable to upload:%s to %s' % (src, dest))


    def link(self, lfn, dir):
        lfn = self.datadir + lfn
        dir = self.datadir + dir
        _logger.debug('HPC: Try to link file from %s to %s' % (lfn, dir))
        try:
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out = proc.communicate("ssh -i %s %s@%s 'mkdir -p %s && ln -s %s %s'" % (self.key, self.user, self.host, dir, lfn, dir))

        except:
            _logger.error('Unable to link:%s to %s' % (lfn, dir))