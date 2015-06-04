from common.NrckiLogger import NrckiLogger

_logger = NrckiLogger().getLogger("DDM")

class SEFactory:
    def __init__(self):
        pass

    def getSE(self, slabel, params={}):
        label = slabel.split(':')[0]
        try:
            if label == 'dropbox':
                from ddm.DropboxSEPlugin import DropboxSEPlugin
                se = DropboxSEPlugin(params)

            elif label == 'grid':
                from ddm.GridSEPlugin import GridSEPlugin
                se = GridSEPlugin(params)

            elif label == 'local':
                from ddm.LocalSEPlugin import LocalSEPlugin
                se = LocalSEPlugin(params)

            elif label == 'http':
                from ddm.HttpSEPlugin import HttpSEPlugin
                se = HttpSEPlugin(params)

            elif label == 'ftp':
                from ddm.FtpSEPlugin import FtpSEPlugin
                se = FtpSEPlugin(params)

            elif label == 'hpc':
                from ddm.HPCSEPlugin import HPCSEPlugin
                se = HPCSEPlugin(params)

            else:
                se = SEPlugin()
        except Exception:
            print Exception.message
            _logger('Unable to get %s instance: %s' % (label, str(Exception.message)))
            return None
        return se

class SEPlugin(object):
    def __init__(self, params=None):
        pass

    def get(self, src, dest, fsize, fsum):
        _logger("SEPlugin.get not implemented")
        raise NotImplementedError("SEPlugin.get not implemented")

    def put(self, src, dest):
        _logger("SEPlugin.put not implemented")
        raise NotImplementedError("SEPlugin.put not implemented")

    def link(self, lfn, dir):
        _logger("SEPlugin.link not implemented")
        raise NotImplementedError("SEPlugin.link not implemented")