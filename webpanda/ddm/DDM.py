from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.core import WebpandaError

_logger = NrckiLogger().getLogger("DDM")


class SEFactory:
    def __init__(self):
        pass

    def getSE(self, plugin, params=None):
        try:
            if plugin in ['dropbox']:
                from webpanda.ddm.DropboxSEPlugin import DropboxSEPlugin
                se = DropboxSEPlugin(params)

            elif plugin in ['grid']:
                from webpanda.ddm.GridSEPlugin import GridSEPlugin
                se = GridSEPlugin(params)

            elif plugin in ['local']:
                from webpanda.ddm.LocalSEPlugin import LocalSEPlugin
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

            else:
                raise Exception('SE needs to be set. Unable to get SE plugin')

        except Exception:
            _logger.error('Unable to get %s instance: %s' % (plugin, str(Exception.message)))
            return SEPlugin()
        return se


class SEPlugin(object):
    def __init__(self, params=None):
        pass

    def get(self, src, dest):
        raise WebpandaError("SEPlugin.get not implemented")

    def put(self, src, dest):
        raise WebpandaError("SEPlugin.put not implemented")

    def link(self, lfn, dir, rel=True):
        raise WebpandaError("SEPlugin.link not implemented")

    def mv(self, lfn, lfn2, rel=True):
        raise WebpandaError("SEPlugin.mv not implemented")

    def rm(self, lfn, rel=True):
        raise WebpandaError("SEPlugin.rm not implemented")

    def ls(self, path, rel=True):
        raise WebpandaError("SEPlugin.ls not implemented")

    def fsize(self, path, rel=True):
        raise WebpandaError("SEPlugin.fsize not implemented")

    def md5sum(self, path, rel=True):
        raise WebpandaError("SEPlugin.md5sum not implemented")

    def adler32(self, path, rel=True):
        raise WebpandaError("SEPlugin.adler32 not implemented")