import subprocess
from common.NrckiLogger import NrckiLogger
from nrckiclient import config

_logger = NrckiLogger().getLogger("DDM")

class HPCSEPlugin():
    def __init__(self, params=None):
        self.key = config['HPC_KEY']
        self.host = config['HPC_HOST']
        self.user = config['HPC_USER']
        self.datadir = config['HPC_DATADIR']

    def get(self, src, dest):
        _logger.debug('HPC: Try to get file from %s to %s' % (src, dest))
        try:
            if not src.startwith('/'):
                src = '/' + src
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            #out = proc.communicate('scp -i %s %s@%s:%s%s %s' % (self.key, self.user, self.host, self.datadir, src, dest))
            out = proc.communicate("rsync -av -e 'ssh -i %s' %s@%s:%s%s %s/" % (self.key, self.user, self.host, self.datadir, src, dest))

        except:
            _logger.error('Unable to download:%s to %s' % (src, dest))


    def put(self, src, dest):
        _logger.debug('HPC: Try to put file from %s to %s' % (src, dest))
        try:
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            #out = proc.communicate('scp -i %s %s %s@%s:%s%s' % (self.key, self.user, self.host, self.datadir, src, dest))
            out = proc.communicate("rsync -av -e 'ssh -i %s' %s %s@%s:%s%s/" % (self.key, src, self.user, self.host, self.datadir, dest))

        except:
            _logger.error('Unable to upload:%s to %s' % (src, dest))
