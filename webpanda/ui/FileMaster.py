import os
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
from webpanda.ddm.DDM import ddm_checkifexists, ddm_localmakedirs, ddm_localcp, ddm_localextractfile

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
   
    def uploadContainer(self, ftp_dir, scope, cont_guid):
	s = DB().getSession()
	container = s.query(Container).filter(Container.guid == cont_guid).one()
	old_status = container.status
	
	if old_status != 'open':
	    raise Exception("Invalid container status (not open): {}".format(old_status))
	
	# Set uploading container status
	container.status = 'uploading'
	s.add(container)
	s.commit()
	
	# Register ftp filesr
	self.register_ftp_files(ftp_dir, scope, container.guid)
	
	# Set open container status
	container.status = old_status
	s.add(container)
	s.commit()
	s.close()
	return 0

    def registerLocalFile(self, arg, dirname, names, scope):
    	"""Register files from local dir to container
    	:param arg: Container guid
    	:param dirname: Abs dir
    	:param names: File name
    	:param scope: Scope to upload files in
    	:return:
    	"""
    	s = DB().getSession()
    	site = s.query(Site).filter(Site.se == client_config.DEFAULT_SE).first()
    	_logger.debug(str(arg))
    	cont = s.query(Container).filter(Container.guid == arg).first()
    	files = cont.files

    	for name in names:
            fpath = os.path.join(dirname, name)

            fobj = None
            # Check in container
            for file in files:
            	if file.lfn == name:
                    fobj = file

            # Check in catalog
            if not fobj:
            	destination = os.path.join(dirname, name)
            	adler = adler32(destination)
            	md5 = md5sum(destination)
            	size = fsize(destination)
            	file_id = ddm_checkifexists(name, size, adler, md5)

            	if file_id:
                    # If file exists
                    fobj = s.query(File).filter(File.id == file_id).one()

            if not fobj:
            	fobj = File()
            	fobj.scope = scope
            	fobj.lfn = name
            	fobj.guid = getGUID(fobj.scope, fobj.lfn)
            	fobj.type = 'input'
            	fobj.status = 'defined'
            	s.add(fobj)
            	s.commit()
            	setFileMeta(fobj.id, fpath)

            cont.files.append(fobj)
            s.add(cont)
            s.commit()

            replicas = fobj.replicas
            replica = None
            for r in replicas:
            	if r.se == site.se and r.status == 'ready':
                    replica = r
            if not replica:
            	ldir = '/' + os.path.join('system', fobj.scope, fobj.guid)
            	ddm_localmakedirs(ldir)
            	ddm_localcp(fpath[len(site.datadir):], ldir)

            	replica = Replica()
            	replica.se = site.se
            	replica.status = 'ready'
            	replica.token = ''
            	replica.lfn = os.path.join(ldir, fobj.lfn)
            	replica.original = fobj
            	s.add(replica)
            	s.commit()
        s.close()

    def register_ftp_files(self, ftp_dir, scope, guid):
    	"""
    	Walks through ftp dir and registers all files
    	:param ftp_dir: Relative ftpdir path
    	:param scope: Files' scope
    	:param guid: Container's guid to register in
    	:return:
    	"""
    	if ftp_dir == '':
            return []

    	ftp_dir_full = os.path.join(client_config.UPLOAD_FOLDER, scope, ftp_dir)

    	ftp_walk = os.walk(ftp_dir_full)
    	for item in ftp_walk:
            # Calculate files' hash, size
            # Register it If db hasn't similar file
            self.registerLocalFile(guid, item[0], item[2], scope)


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

@celery.task(serializer='json')
def async_uploadContainer(ftp_dir, scope, cont_guid):
    fm = FileMaster()
    res = None
#    try:
    res = fm.uploadContainer(ftp_dir, scope, cont_guid)
#    except Exception as e:
#	raise async_uploadContainer.retry(countdown=60, exc=e, max_retries=5)
    return json.dumps(res)

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
