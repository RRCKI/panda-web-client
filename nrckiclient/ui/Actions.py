import commands
import os
import subprocess
import shutil
from ..common.NrckiLogger import NrckiLogger
from ..ddm.DDM import SEFactory
from nrckiclient import config

DATA_DIR = config['DATA_DIR']

_logger = NrckiLogger().getLogger("Actions")


def movedata(params, fileList, fromType, fromParams, toType, toParams):
    if len(fileList) == 0:
        _logger.debug('No files to move')
        return 0, 'No files to move'

    tmpdir = commands.getoutput("uuidgen")

    if 'compress' in params.keys() and 'tgzname' in params.keys():
        compress = params['compress']
        tmpTgzName = params['tgzname']
    else:
        compress = False

    if 'dest' not in toParams.keys():
        _logger.error('Attribute error: dest')
        return 1, 'Attribute error: dest'
    dest = toParams['dest']

    sefactory = SEFactory()
    fromSE = sefactory.getSE(fromType, fromParams)
    toSE = sefactory.getSE(toType, toParams)

    tmphome = "%s/%s" % (DATA_DIR, tmpdir)
    if not os.path.isdir(tmphome):
        os.makedirs(tmphome)

    tmpout = []
    tmpoutnames = []
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


    print 'Need compress? ' + str(compress)
    if compress:
        _logger.debug('Compress start: ')
        tmpTgz = os.path.join(tmphome, tmpTgzName)
        _logger.debug('TGZ file = ' + tmpTgz)
        wd = os.getcwd()
        os.chdir(tmphome)
        proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate("tar -cvzf %s *" % tmpTgz)
        tmpout = [tmpTgz]
        tmpoutnames = [tmpTgzName]
        os.chdir(wd)
        _logger.debug('Compress finish:')

    for f in tmpout:
        #put file to SE
        toSE.put(f, dest)

    shutil.rmtree(tmphome)
    return 0, tmpoutnames