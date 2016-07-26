import commands
import os
from datetime import datetime

from webpanda.common import client_config
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.common.utils import adler32, md5sum, fsize
from webpanda.core import WebpandaError
from webpanda.ddm.DDM import SEFactory
from webpanda.ddm.scripts import ddm_localmakedirs, ddm_localcp, ddm_checkifexists, ddm_localrmtree, \
    ddm_getlocalfilemeta, ddm_localisdir
from webpanda.fc import scripts as fc
from webpanda.files import File, Replica
from webpanda.services import files_, conts_, sites_, replicas_, users_

DATA_DIR = client_config.TMP_DIR
_logger = NrckiLogger().getLogger("files.scripts")


def cloneReplica(replicaid, se):
    replica = replicas_.get(replicaid)
    file = replica.original
    replicas = file.replicas
    for r in replicas:
        if se == r.se:
            _logger.debug('Replica exists: id=%s' % r.id)
            # Update expired time
            return r.id

    # Define base replica
    from_se = sites_.first(se=replica.se)
    fromParams = {}
    if replica.status == 'link':
        lfn = getLinkLFN(file.scope, replica.lfn)
    else:
        lfn = replica.lfn

    # Define result replica params
    to_se = sites_.first(se=se)
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
        replicas_.save(r)
        file.modification_time = datetime.utcnow()
        file.replicas.append(r)
        files_.save(file)

        for cont in file.containers:
            linkReplica(r.id, '/%s/%s' % (client_config.DEFAULT_SCOPE, cont.cont.guid))

        return r.id
    raise Exception('movedata return code: %s' % ec)


def copyReplica(replicaid, se, path):
    id = cloneReplica(replicaid, se)
    linkReplica(id, path)
    return 0


def linkReplica(replicaid, dir):
    replica = replicas_.get(replicaid)
    site = sites_.first(se=replica.se)
    lfn = replica.lfn
    linkdata(site.plugin, {}, lfn, dir)
    return 0


def uploadContainer(ftp_dir, scope, cont_guid):
    container = conts_.first(guid=cont_guid)
    old_status = container.status

    if old_status != 'open':
        raise Exception("Invalid container status (not open): {}".format(old_status))

    # Set uploading container status
    container.status = 'uploading'
    conts_.save(container)

    # Register ftp filesr
    register_ftp_files(ftp_dir, scope, container.guid)

    # Set open container status
    container.status = old_status
    conts_.save(container)
    return 0


def registerLocalFile(arg, dirname, names, scope):
    """Register files from local dir to container
    :param arg: Container guid
    :param dirname: Abs dir
    :param names: File name
    :param scope: Scope to upload files in
    :return:
    """
    site = sites_.first(se=client_config.DEFAULT_SE)
    _logger.debug(str(arg))
    cont = conts_.first(guid=arg)
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
                fobj = files_.get(file_id)

        if not fobj:
            fobj = File()
            fobj.scope = scope
            fobj.lfn = name
            fobj.guid = getGUID(fobj.scope, fobj.lfn)
            fobj.type = 'input'
            fobj.status = 'defined'
            files_.save(fobj)
            setFileMeta(fobj.id, fpath)

        # Register file in catalog
        fc.reg_file_in_cont(fobj, cont, "input")

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
            replicas_.save(replica)


def register_ftp_files(ftp_dir, scope, guid):
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
        registerLocalFile(guid, item[0], item[2], scope)


def linkFile(fileid, se, dir):
    f = files_.get(fileid)
    replicas = f.replicas
    for replica in replicas:
        if replica.se == se:
            linkReplica(replica.id, dir)
            return
    raise Exception('No replica to link file:%s on SE:%s' % (f.guid, se))


def getScope(username):
    """
    Get default user's scope
    :param username:
    :return: str
    """
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
    f = files_.get(fileid)
    if f.fsize == None:
        f.fsize = fsize(lfn)
    if f.md5sum == None:
        f.md5sum = md5sum(lfn)
    if f.checksum == None:
        f.checksum = adler32(lfn)
    f.modification_time = datetime.utcnow()
    files_.save(f)


def getLinkLFN(scope, url):
    fname = url.split('/')[-1]
    guid = getGUID(scope, fname)
    return '/system/%s/%s/%s' % (scope, guid, fname)


def movedata(params, fileList, from_plugin, from_params, to_plugin, to_params):
    _logger.debug('FROM_PLUGIN')
    _logger.debug(from_plugin)
    _logger.debug(str(from_params))
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


def upload_dir(user_id, cont_id, se_id, path):
    """
    Uploads files from external dir path into defined contained
    :param cont_id: id of Container
    :param se_id: id of SE
    :param path: dir path on SE
    :return:
    """
    user = users_.get(user_id)
    cont = conts_.get(cont_id)
    se = sites_.get(se_id)

    # Initialize SE connector
    print "=Initialize SE connector"
    conn_factory = SEFactory()
    connector = conn_factory.getSE(se.plugin, None)

    # Fetch list of files
    print "=Fetch list of files"
    try:
        list_of_lfn = connector.ls(path, rel=False)
        for item in list_of_lfn:
            # Check empty items
            if item == "":
                list_of_lfn.remove(item)
    except:
        raise WebpandaError("Unable to get list of files from SE: " + str(se_id))
    print "=" + str(len(list_of_lfn))

    # Create list of File objs
    print "=Create list of File objs"
    list_of_obj = list()
    for item in list_of_lfn:
        list_of_obj.append(fc.new_file(user, item))
    print "=" + str(len(list_of_obj))

    # Iterate through files objects
    print "=IterateLoop:Start"
    for item in list_of_lfn:
        # Add files to container:
        print "=Add file to container"
        fc.reg_file_in_cont(item, cont, 'intermediate')

        # Copy files into system dir
        print "=Copy file into system dir"
        connector.link(os.path.join(path, item.lfn), fc.get_file_dir(item))

        # Calculate fsize, adler32, md5hash
        print "=Calculate fsize, adler32, md5hash"
        item.fsize = connector.fsize(fc.get_file_path(item))
        item.md5sum = connector.md5sum(fc.get_file_path(item))
        item.checksum = connector.adler32(fc.get_file_path(item))
        fc.save(item)

        # Create list of Replica objs
        print "=Create Replica object"
        r = fc.new_replica(item, se)
        r.status = 'ready'
        fc.save(r)

        # Update files' status
        print "=Update files' status"
        item.status = 'ready'
        fc.save(item)
    print "=IterateLoop:Finish"

    # Return container id
    print "=Return container id"
    return cont_id