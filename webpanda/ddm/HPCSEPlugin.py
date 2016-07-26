import subprocess

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.common import client_config
from webpanda.core import WebpandaError
from webpanda.ddm.DDM import SEPlugin
from webpanda.ddm.scripts import ddm_getlocalabspath

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
            out = proc.communicate("rsync --bwlimit=2500 -av -e 'ssh -i %s' %s@%s:%s %s/" % (self.key, self.user, self.host, src, dest))
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
            out = proc.communicate("rsync --bwlimit=2500 -av -e 'ssh -i %s' %s %s@%s:%s/" % (self.key, src, self.user, self.host, dest))

        except:
            _logger.error('Unable to upload:%s to %s' % (src, dest))

    def link(self, lfn, d, rel=True):
        if rel:
            lfn = self.datadir + lfn
        d = self.datadir + d
        _logger.debug('HPC: Try to link file from %s to %s' % (lfn, d))
        try:
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out = proc.communicate("ssh -i %s %s@%s 'mkdir -p %s && ln -s %s %s'" % (self.key, self.user, self.host, d, lfn, d))
            return True
        except:
            _logger.error('Unable to link:%s to %s' % (lfn, d))
            raise WebpandaError('Unable to link:%s to %s' % (lfn, d))

    def ls(self, path, rel=True):
        if rel:
            path = self.datadir + path
        _logger.debug('HPC: Try to list files in path %s' % (path))

        try:
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out = proc.communicate("ssh -i {key} {user}@{host} 'ls -p {path} | grep -v /'".format(key=self.key, user=self.user, host=self.host, path=path))
            _logger.debug(out[0])
            return out[0].split('\n')
        except OSError:
            _logger.error('Unable to list files in: %s' % (path))
            raise WebpandaError('Unable to list files in: %s' % (path))

    def fsize(self, path, rel=True):
        if rel:
            path = self.datadir + path
        _logger.debug('HPC: Trying to get file size of file: %s' % (path))

        cmd = "ssh -i {key} {user}@{host} 'stat -Lc %s {path}'".format(key=self.key, user=self.user, host=self.host, path=path)
        _logger.debug(cmd)

        try:
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out = proc.communicate(cmd)
            _logger.debug(out[0])
            _logger.debug(out[1])
            return out[0]
        except OSError:
            _logger.error('Unable to get file size: %s' % (path))
            raise WebpandaError('Unable to get file size: %s' % (path))

    def md5sum(self, path, rel=True):
        if rel:
            path = self.datadir + path
        _logger.debug('HPC: Trying to get md5sum of file: %s' % (path))

        cmd = "ssh -i {key} {user}@{host} 'md5sum {path}'".format(key=self.key, user=self.user, host=self.host, path=path)
        _logger.debug(cmd)

        try:
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out = proc.communicate(cmd)
            _logger.debug(out[0])
            _logger.debug(out[1])
            return out[0].split(' ')[0]
        except OSError:
            _logger.error('Unable to calculate md5: %s' % (path))
            raise WebpandaError('Unable to calculate md5: %s' % (path))

    def adler32(self, path, rel=True):
        if rel:
            path = self.datadir + path
        _logger.debug('HPC: Trying to get adler32 of file: %s' % (path))

        cmd = "TODO:add script"
        _logger.debug(cmd)

        try:
            proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            # out = proc.communicate("ssh -i {key} {user}@{host} 'ls -p {path} | grep -v /'".format(key=self.key, user=self.user, host=self.host, path=path))
            #_logger.debug(out[0])
            #_logger.debug(out[1])
            # return out[0].split('\n')
            return "testtest"
        except OSError:
            _logger.error('Unable to calculate adler32: %s' % (path))
            raise WebpandaError('Unable to calculate adler32: %s' % (path))

