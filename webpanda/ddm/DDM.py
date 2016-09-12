from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.ddm.LocalSEPlugin import LocalSEPlugin

_logger = NrckiLogger().getLogger("DDM")

class SEFactory:
    def __init__(self):
        pass

    def getSE(self, plugin, params={}):
        try:
            if plugin in ['dropbox']:
                from webpanda.ddm.DropboxSEPlugin import DropboxSEPlugin
                se = DropboxSEPlugin(params)

            elif plugin in ['grid']:
                from webpanda.ddm.GridSEPlugin import GridSEPlugin
                se = GridSEPlugin(params)

            elif plugin in ['local']:
                se = LocalSEPlugin(params)

            elif plugin in ['http', 'https']:
                from webpanda.ddm.HttpSEPlugin import HttpSEPlugin
                se = HttpSEPlugin(params)

            elif plugin in ['ftp']:
                from webpanda.ddm.FtpSEPlugin import FtpSEPlugin
                se = FtpSEPlugin(params)

            elif plugin in ['hpc']:
                from webpanda.ddm.HPCSEPlugin import HPCSEPlugin
                se = HPCSEPlugin(params)

            elif plugin in ['tobeset']:
                raise Exception('SE needs to be set. Unable to get SE plugin')

        except Exception:
            _logger.error('Unable to get %s instance: %s' % (plugin, str(Exception.message)))
            return SEPlugin()
        return se


class SEPlugin(object):
    def __init__(self, params=None):
        pass

    def get(self, src, dest, fsize, fsum):
        _logger.error("SEPlugin.get not implemented")
        raise NotImplementedError("SEPlugin.get not implemented")

    def put(self, src, dest):
        _logger.error("SEPlugin.put not implemented")
        raise NotImplementedError("SEPlugin.put not implemented")

    def link(self, lfn, dir, rel=True):
        _logger.error("SEPlugin.link not implemented")
        raise NotImplementedError("SEPlugin.link not implemented")

    def ls(self, path, rel=True):
        _logger.error("SEPlugin.ls not implemented")
        raise NotImplementedError("SEPlugin.ls not implemented")

    def fsize(self, path, rel=True):
        _logger.error("SEPlugin.fsize not implemented")
        raise NotImplementedError("SEPlugin.fsize not implemented")

    def md5sum(self, path, rel=True):
        _logger.error("SEPlugin.md5sum not implemented")
        raise NotImplementedError("SEPlugin.md5sum not implemented")

    def adler32(self, path, rel=True):
        _logger.error("SEPlugin.adler32 not implemented")
        raise NotImplementedError("SEPlugin.adler32 not implemented")