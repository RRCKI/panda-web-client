import os
import shutil
from common import client_config
from common.NrckiLogger import NrckiLogger
from common.utils import adler32, fsize
from common.utils import md5sum
from db.models import DB, File

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

def ddm_getlocalfilemeta(path):
    """
    returns file metadata
    :param path:
    :return:
    """
    abspath = ddm_getlocalabspath(path)
    data = {}
    data['checksum'] = adler32(abspath)
    data['md5sum'] = md5sum(abspath)
    data['fsize'] = fsize(abspath)
    return data

def ddm_localisdir(ldir):
    """
    os.path.isdir for ddm dir
    :param ldir:
    :return:
    """
    absdir = ddm_getlocalabspath(ldir)
    return os.path.isdir(absdir)

def ddm_localmakedirs(ldir):
    """
    os.makedirs for ddm dir
    :param ldir:
    :return:
    """
    absdir = ddm_getlocalabspath(ldir)
    return os.makedirs(absdir)

def ddm_localrmtree(ldir):
    """
    shutil.rmtree for ddm dir
    :param dir:
    :return:
    """
    absdir = ddm_getlocalabspath(ldir)
    shutil.rmtree(absdir)

def ddm_checkifexists(name, size, adler, md5):
    """
    Checks if file with size and sums exixts in catalog
    :return:
    """
    s = DB().getSession()
    n = s.query(File).filter(File.checksum == adler).filter(File.md5sum == md5).filter(File.fsize == size).count()
    if n == 0:
        s.close()
        return 0
    file = s.query(File).filter(File.checksum == adler).filter(File.md5sum == md5).filter(File.fsize == size).one()
    s.close()
    return file.id