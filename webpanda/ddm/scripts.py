import os
import shutil
import tarfile

from webpanda.common import client_config
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.common.utils import adler32, fsize
from webpanda.common.utils import md5sum
from webpanda.db.models import DB, File, Replica

_logger = NrckiLogger().getLogger("DDM")

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
    return shutil.rmtree(absdir)

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
    file = s.query(File).filter(File.checksum == adler).filter(File.md5sum == md5).filter(File.fsize == size).first()
    #file = s.query(File).filter(File.checksum == adler).filter(File.md5sum == md5).filter(File.fsize == size).one()
    s.close()
    return file.id

def ddm_checkexternalifexists(storage, lfn):
    """
    Checks if external file exixts in catalog
    :return:
    """
    s = DB().getSession()
    n = s.query(Replica).filter(Replica.status == 'link').filter(Replica.lfn == lfn).count()
    if n == 0:
        s.close()
        return 0
    replica = s.query(Replica).filter(Replica.status == 'link').filter(Replica.lfn == lfn).first()
    file = replica.original
    s.close()
    return file.id

def ddm_localcp(src, dest):
    """
    shutil.copy2 for ddm file
    :param src:
    :param dest:
    :return:
    """
    asrc = ddm_getlocalabspath(src)
    adest = ddm_getlocalabspath(dest)
    return shutil.copy2(asrc, adest)

def ddm_localextractfile(f):
    """
    tar -xf for local ddm file
    :param f: rel file path
    :return:
    """
    af = ddm_getlocalabspath(f)
    afdir = '/'.join(af.split('/')[:-1])
    t = tarfile.open(af, 'r')
    t.extractall(afdir)