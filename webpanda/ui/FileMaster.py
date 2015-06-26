import commands
from common import client_config
from datetime import datetime
import json
from app import celery
from common.NrckiLogger import NrckiLogger
from common.utils import adler32, md5sum, fsize
from ui.Actions import movedata, linkdata
from mq.MQ import MQ
from db.models import *
import os

_logger = NrckiLogger().getLogger("FileMaster")

class FileMaster:
    def __init__(self):
        self.table_files = 'files'

    def makeReplica(self, fileid, se):
        s = DB().getSession()
        file = s.query(File).filter(File.id == fileid).one()
        replica = Replica()
        rvalue = 0

        # Define file params
        from_plugin = file.se
        fromParams = {'token': file.token}

        # Define result replica params
        to_se = s.query(Site).filter(Site.se == se).first()
        dest = '/' + client_config.DEFAULT_SCOPE + '/' + file.guid
        toParams = {'dest': dest}

        ec, filesinfo = movedata({}, [file.lfn], from_plugin, fromParams, to_se.plugin, toParams)
        if ec == 0:
            replica.se = se
            replica.status = 'ready'
            replica.lfn = os.path.join(dest, file.lfn.split('/')[-1])
            s.add(replica)
            s.commit()
            file.replicas.append(replica)
            file.fsize = filesinfo[file.lfn]['fsize']
            file.md5sum = filesinfo[file.lfn]['md5sum']
            file.checksum = filesinfo[file.lfn]['checksum']
            file.modification_time = datetime.utcnow()
            s.add(file)
            s.commit()
            rvalue = replica.id
        s.close()
        return rvalue

    def cloneReplica(self, replicaid, se):
        s = DB().getSession()
        replica = s.query(Replica).filter(Replica.id == replicaid).one()
        file = replica.original
        replicas = file.replicas
        for r in replicas:
            if se == r.se:
                _logger.debug('Replica exists: id=%s' % r.id)
                # Update expired time
                return r.id

        # Define base replica
        from_se = s.query(Site).filter(Site.se == replica.se).first()
        fromParams = {}

        # Define result replica params
        to_se = s.query(Site).filter(Site.se == se).first()
        dest = '/'.join(replica.lfn.split('/')[:-1])
        toParams = {'dest': dest}

        ec, filesinfo = movedata({}, [replica.lfn], from_se.plugin, fromParams, to_se.plugin, toParams)
        if ec == 0:
            r = Replica()
            if file.fsize is None:
                file.fsize = filesinfo[replica.lfn]['fsize']
            if file.md5sum is None:
                file.md5sum = filesinfo[replica.lfn]['md5sum']
            if file.checksum is None:
                file.checksum = filesinfo[replica.lfn]['checksum']
            r.se = se
            r.status = 'ready'
            r.lfn = replica.lfn
            s.add(r)
            s.commit()
            file.modification_time = datetime.utcnow()
            file.replicas.append(r)
            s.add(file)
            s.commit()
            return r.id
        s.close()
        raise Exception('movedata return code: %s' % ec)
        return ec

    def copyReplica(self, replicaid, se, path):
        id = cloneReplica(replicaid, se)
        linkReplica(id, path)
        return 0

    def linkReplica(self, replicaid, dir):
        s = DB().getSession()
        replica = s.query(Replica).filter(Replica.id == replicaid).one()
        site = s.query(Site).filter(Site.se == replica.se).first()
        lfn = replica.lfn
        linkdata(site.plugin, {}, lfn, dir)
        s.close()



@celery.task
def cloneReplica(replicaid, se):
    fm = FileMaster()
    return fm.cloneReplica(replicaid, se)

@celery.task
def makeReplica(fileid, se):
    fm = FileMaster()
    return fm.makeReplica(fileid, se)

@celery.task
def linkReplica(replicaid, dir):
    fm = FileMaster()
    return fm.linkReplica(replicaid, dir)

@celery.task
def copyReplica(replicaid, se, path):
    fm = FileMaster()
    return fm.copyReplica(replicaid, se, path)

def linkFile(fileid, se, dir):
    s = DB().getSession()
    file = s.query(File).filter(File.id == fileid).one()
    replicas = file.replicas
    for replica in replicas:
        if replica.se == se:
            linkReplica(replica.id, dir)
            return
    raise Exception('No replica to link file:%s on SE:%s' % (file.guid, se))
    s.close()
    return

def mqCloneReplica(replicaid, se):
    routing_key = client_config.MQ_FILEKEY + '.clone'
    mq = MQ(host=client_config.MQ_HOST, exchange=client_config.MQ_EXCHANGE)
    # Create MQ request
    data = {}
    data['replicaid'] = replicaid
    data['se'] = se
    message = json.dumps(data)
    print '%s: %s %s' % ('mqCloneReplica', replicaid, se)
    mq.sendMessage(message, routing_key)

def mqMakeReplica(fileid, se):
    routing_key = client_config.MQ_FILEKEY + '.make'
    mq = MQ(host=client_config.MQ_HOST, exchange=client_config.MQ_EXCHANGE)
    # Create MQ request
    data = {}
    data['fileid'] = fileid
    data['se'] = se
    message = json.dumps(data)
    print '%s: %s %s' % ('mqMakeReplica', fileid, se)
    mq.sendMessage(message, routing_key)

def getScope(username):
    return 'web.' + username

def getGUID(scope, lfn):
    guid = commands.getoutput('uuidgen')
    return scope + '_' + guid

def getFullPath(scope, dataset, lfn):
    if ':' in dataset:
        return '/' + '/'.join(dataset.split(':') + [lfn])
    return '/' + '/'.join([scope, dataset, lfn])

def getUrlInfo(url):
    # Format - se:path:token
    parts = url.split(':')
    if len(parts) == 2:
        se = parts[0]
        path = parts[1]
        token = ""
    elif len(parts) == 3:
        se = parts[0]
        path = parts[1]
        token = parts[2]
    else:
        raise Exception('Illegal URL format')
    return se, path, token

def getFtpLink(lfn):
    header = client_config.FTP
    result = ''
    return result

def setFileMeta(fileid, lfn):
    s = DB().getSession()
    file = s.query(File).filter(File.id == fileid).one()
    if file.fsize == None:
        file.fsize = fsize(lfn)
    if file.md5sum == None:
        file.md5sum = md5sum(lfn)
    if file.checksum == None:
        file.checksum = adler32(lfn)
    file.modification_time = datetime.utcnow()
    s.add(file)
    s.commit()
    s.close()