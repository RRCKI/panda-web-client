import commands
import os
import shutil
from common.NrckiLogger import NrckiLogger
from ddm.DDM import SEFactory, ddm_getlocalfilemeta, ddm_localisdir, ddm_localmakedirs, ddm_localrmtree
from common import client_config

DATA_DIR = client_config.TMP_DIR

_logger = NrckiLogger().getLogger("Actions")


def movedata(params, fileList, from_plugin, from_params, to_plugin, to_params):
    if len(fileList) == 0:
        _logger.debug('No files to move')
        return 0, 'No files to move'

    tmpdir = commands.getoutput("uuidgen")

    if 'dest' not in to_params.keys():
        _logger.error('Attribute error: dest')
        return 1, 'Attribute error: dest'
    dest = to_params['dest']

    sefactory = SEFactory()
    fromSE = sefactory.getSE(from_plugin, from_params)
    toSE = sefactory.getSE(to_plugin, to_params)

    tmphome = "/%s/%s" % (DATA_DIR, tmpdir)

    if not ddm_localisdir(tmphome):
        ddm_localmakedirs(tmphome)

    tmpout = []
    tmpoutnames = []
    filesinfo = {}
    for f in fileList:
        if '/' in f:
            fname = f.split('/')[-1]
        elif ':' in f:
            fname = f.split(':')[-1]
        else:
            fname = f

        tmpfile = os.path.join(tmphome, fname)
        fromSE.get(f, tmphome)
        tmpout.append(tmpfile)
        tmpoutnames.append(fname)

        # Collect file info
        filesinfo[f] = ddm_getlocalfilemeta(tmpfile)

    for f in tmpout:
        #put file to SE
        toSE.put(f, dest)

    ddm_localrmtree(tmphome)
    return 0, filesinfo

def linkdata(setype, separams, lfn, dir):
    sefactory = SEFactory()
    se = sefactory.getSE(setype, separams)
    se.link(lfn, dir)

