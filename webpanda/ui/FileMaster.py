from common import client_config
from datetime import datetime
import json
from app import celery
from ui.Actions import movedata, linkdata
from mq.MQ import MQ
from db.models import *
import os


class FileMaster:
    def __init__(self):
        self.table_files = 'files'

    def makeReplica(self, fileid, se):
        s = DB().getSession()
        file = s.query(File).filter(File.id == fileid).one()
        replica = Replica()
        rvalue = 0
        fromParams = {'token': file.token}
        dest = '/' + client_config.DEFAULT_SCOPE + '/' + file.guid
        toParams = {'dest': dest}
        ec, filesinfo = movedata({}, [file.lfn], file.se, fromParams, se, toParams)
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
                print 'Replica is ready'
                # Update expired time
                return r.id
        fromParams = {}
        dest = '/' + client_config.DEFAULT_SCOPE + '/' + file.guid
        toParams = {'dest': dest}

        ec, filesinfo = movedata({}, [replica.lfn], replica.se, fromParams, se, toParams)
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