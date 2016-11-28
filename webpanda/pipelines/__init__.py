class BasicPipeline():
    def __init__(self, pp, params):
        self.pp = pp
        for tmpKey, tmpVal in params.iteritems():
            setattr(self, tmpKey, tmpVal)

    def init(self):
        return None

    def pre(self):
        return None

    def split(self):
        return None

    def prun(self):
        return None

    def merge(self):
        return None

    def post(self):
        return None

    def finish(self):
        return None