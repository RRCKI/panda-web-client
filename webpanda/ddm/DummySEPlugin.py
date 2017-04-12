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
