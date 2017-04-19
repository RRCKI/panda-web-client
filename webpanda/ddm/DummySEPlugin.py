from webpanda.common.NrckiLogger import NrckiLogger

_logger = NrckiLogger().getLogger("DDM")

class DummySEPlugin():
    def __init__(self, params={}):
        self.params = params

    def get(self, src, dest):
        return True

    def put(self, src, dest):
        return True

    def link(self, lfn, dir):
        return True

    def mv(self, lfn, lfn2, rel=True):
        return True

    def rm(self, lfn, rel=True):
        return True

    def ls(self, path, rel=True):
        return True

    def fsize(self, path, rel=True):
        return None

    def md5sum(self, path, rel=True):
        return None

    def adler32(self, path, rel=True):
        return None