import os
from common import client_config
from common.NrckiLogger import NrckiLogger
from common.utils import adler32, fsize
from common.utils import md5sum

_logger = NrckiLogger().getLogger("DDM")

class SEFactory:
    def __init__(self):
        pass

    def getSE(self, plugin, params={}):
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
            _logger.error('Unable to get %s instance: %s' % (plugin, str(Exception.message)))
            return None
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

    def link(self, lfn, dir):
        _logger.error("SEPlugin.link not implemented")
        raise NotImplementedError("SEPlugin.link not implemented")

def ddm_getlocalabspath(path):
    localdir = client_config.DATA_PATH
    if path.startswith('/'):
        return localdir + path
    return os.path.join(localdir, path)

def ddm_getlocalfilemeta(relpath):
    abspath = ddm_getlocalabspath(relpath)
    data = {}
    data['checksum'] = adler32(abspath)
    data['md5sum'] = md5sum(abspath)
    data['fsize'] = fsize(abspath)
    return data

def ddm_localisdir(dir):
    absdir = ddm_getlocalabspath(dir)
    return os.path.isdir(absdir)

def ddm_localmakedirs(dir):
    absdir = ddm_getlocalabspath(dir)
    return os.path.makedirs(absdir)