from common.NrckiLogger import NrckiLogger
from db.models import DB, Site

_logger = NrckiLogger().getLogger("DDM")

class SEFactory:
    def __init__(self):
        pass

    def getSE(self, ce, params={}):
        s = DB().getSession()
        site = s.query(Site).filter(Site.ce == ce).one()
        plugin = site.plugin
        s.close()
        try:
            if plugin in ['dropbox']:
                from ddm.DropboxSEPlugin import DropboxSEPlugin
                se = DropboxSEPlugin(params)

            elif plugin in ['grid']:
                from ddm.GridSEPlugin import GridSEPlugin
                se = GridSEPlugin(params)

            elif plugin in ['local']:
                from ddm.LocalSEPlugin import LocalSEPlugin
                se = LocalSEPlugin(params)

            elif plugin in ['http', 'https']:
                from ddm.HttpSEPlugin import HttpSEPlugin
                se = HttpSEPlugin(params)

            elif plugin in ['ftp']:
                from ddm.FtpSEPlugin import FtpSEPlugin
                se = FtpSEPlugin(params)

            elif plugin in ['hpc']:
                from ddm.HPCSEPlugin import HPCSEPlugin
                se = HPCSEPlugin(params)

            elif plugin in ['tobeset']:
                raise Exception('SE needs to be set. Unable to get SE plugin')

            else:
                se = SEPlugin()
        except Exception:
            print Exception.message
            _logger('Unable to get %s instance: %s' % (plugin, str(Exception.message)))
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