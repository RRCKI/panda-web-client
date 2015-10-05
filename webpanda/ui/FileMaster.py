import commands
from datetime import datetime
import simplejson as json

from webpanda.app import celery
from webpanda.common import client_config
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.common.utils import adler32, md5sum, fsize
from webpanda.ui.Actions import movedata, linkdata
from webpanda.mq.MQ import MQ
from webpanda.db.models import *

_logger = NrckiLogger().getLogger("FileMaster")

class FileMaster:
    def __init__(self):
        self.table_files = 'files'

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
        if replica.status == 'link':
            lfn = getLinkLFN(file.scope, replica.lfn)
        else:
            lfn = replica.lfn

        # Define result replica params
        to_se = s.query(Site).filter(Site.se == se).first()
        dest = '/'.join(lfn.split('/')[:-1])
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
            r.lfn = lfn
            s.add(r)
            s.commit()
            file.modification_time = datetime.utcnow()
            file.replicas.append(r)
            s.add(file)
            s.commit()

            for cont in file.containers:
                self.linkReplica(r.id, '/%s/%s' % (client_config.DEFAULT_SCOPE, cont.guid))

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
        return 0



@celery.task(serializer='json')
def cloneReplica(replicaid, se):
    fm = FileMaster()
    return json.dumps(fm.cloneReplica(replicaid, se))

@celery.task(serializer='json')
def linkReplica(replicaid, dir):
    fm = FileMaster()
    return json.dumps(fm.linkReplica(replicaid, dir))

@celery.task(serializer='json')
def copyReplica(replicaid, se, path):
    fm = FileMaster()
    return json.dumps(fm.copyReplica(replicaid, se, path))

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

def getScope(username):
    return 'web.' + username

def getGUID(scope, lfn):
    guid = commands.getoutput('uuidgen')
    return scope + '_' + guid

def getFullPath(scope, dataset, lfn):
    if ':' in dataset:
        return '/' + '/'.join([dataset.split(':')[0], '.sys', dataset.split(':')[1], lfn])
    return '/' + '/'.join([scope, '.sys', dataset, lfn])

def getUrlInfo(url):
    # https://www.dropbox.com/get?file=15:dropbox_token=112345AZ
    parts = url.split(':')
    se = parts[0]
    if len(parts) > 3:
        raise Exception('Incorrect url')
        return

    if '?' in parts[1]:
        path = parts[1].split('?')[0]
        token = parts[1].split('?')[1]
    else:
        path = parts[1]
        token = ''

    if len(parts) == 3:
        token = ':'.join(token, parts[2])

    # Removes first leading slash
    path = path[1:]
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

def getLinkLFN(scope, url):
    fname = url.split('/')[-1]
    guid = getGUID(scope, fname)
    return '/system/%s/%s/%s' % (scope, guid, fname)
