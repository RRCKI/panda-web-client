import commands
from common import client_config
from datetime import datetime
import json
from app import celery
from common.NrckiLogger import NrckiLogger
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
        to_se = s.query(Site).filter(Site.se == se).one()
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
                _logger.debug('Replica is ready: id=%s' % r.id)
                # Update expired time
                return r.id

        # Define base replica
        from_se = s.query(Site).filter(Site.se == replica.se).one()
        fromParams = {}

        # Define result replica params
        to_se = s.query(Site).filter(Site.se == se).one()
        dest = '/' + client_config.DEFAULT_SCOPE + '/' + file.guid
        toParams = {'dest': dest}

        ec, filesinfo = movedata({}, [replica.lfn], from_se.plugin, fromParams, to_se.plugin, toParams)
        if ec == 0:
            replica = Replica()
            replica.se = se
            replica.status = 'ready'
            replica.lfn = os.path.join(dest, file.lfn.split('/')[-1])
            s.add(replica)
            s.commit()
            file.replicas.append(replica)
            s.add(file)
            s.commit()
            return replica.id

    def linkReplica(self, replicaid, dir):
        s = DB().getSession()
        replica = s.query(Replica).filter(Replica.id == replicaid).one()
        se = replica.se
        lfn = replica.lfn
        linkdata(se, {}, lfn, dir)

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
    return '/'.join(scope, dataset, lfn)