# -*- coding: utf-8 -*-
import os
import commands
from datetime import datetime

from celery import chord
from flask import jsonify, request, make_response, g, Response

from webpanda.app import app, db, oauth
from webpanda.celery import send_job, copyReplica
from webpanda.ddm.scripts import ddm_getlocalabspath
from webpanda.app.scripts import registerLocalFile, extractLog, register_ftp_files
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.common.utils import find
from webpanda.app.models import Distributive, Container, File, Site, Replica, TaskMeta, Job
from webpanda.ui.FileMaster import getGUID, getFtpLink, setFileMeta
from webpanda.ui.FileMaster import getScope
from webpanda.ui.JobMaster import prepareInputFiles
from webpanda.celery import cloneReplica

_logger = NrckiLogger().getLogger("app.api")

@app.before_request
def before_requestAPI():
    _logger.debug(request.url)

## CLAVIRE ZONE

@app.route('/api/sw', methods=['GET'])
@oauth.require_oauth('api')
def swAPI():
    """Returns list of available software"""
    g.user = request.oauth.user

    ds = Distributive.query.all()
    dlist = []
    for d in ds:
        a = {}
        a['id'] = d.id
        a['name'] = d.name
        a['version'] = d.version
        dlist.append(a)
    return make_response(jsonify({'data': dlist}), 200)

@app.route('/api/container/<guid>/list', methods=['GET'])
@oauth.require_oauth('api')
def contListAPI(guid):
    """Returns list of files registered in container"""
    g.user = request.oauth.user

    cont = Container.query.filter_by(guid=guid).first()
    files = cont.files

    datalist = []
    for file in files:
        data = {}
        data['lfn'] = file.lfn
        data['guid'] = file.guid
        data['modification_time'] = str(file.modification_time)
        data['fsize'] = file.fsize
        data['adler32'] = file.checksum
        data['md5sum'] = file.md5sum
        data['scope'] = file.scope
        datalist.append(data)
    return make_response(jsonify({'data': datalist}), 200)

@app.route('/api/job', methods=['POST'])
@oauth.require_oauth('api')
def jobAPI():
    """Creates new job
    """
    g.user = request.oauth.user
    scope = getScope(request.oauth.user.username)

    js = request.json
    data = js['data']

    distr_id = data['sw_id']
    params = data['script']
    corecount = data['cores']

    site = Site.query.filter_by(ce=app.config['DEFAULT_CE']).first()
    try:
        distr = Distributive.query.filter_by(id=distr_id).one()
    except(Exception):
        _logger.error(Exception.message)
        return make_response(jsonify({'error': 'SW/Container not found'}), 404)

    container = Container()
    guid = 'job.' + commands.getoutput('uuidgen')
    container.guid = guid
    container.status = 'open'
    db.session.add(container)
    db.session.commit()
    
    # Process ftp files
    if 'ftp_dir' in data.keys():
        ftp_dir = data['ftp_dir']
        register_ftp_files(ftp_dir, scope, container.guid)

    # Process guid list
    if 'guids' in data.keys():
        guids = data['guids']
        for f in guids:
            if f != '':
                file_ = File.query.filter_by(guid=f).first()
                if file_ is not None:
                    # Add file to container
                    container.files.append(file_)
                    db.session.add(container)
                    db.session.commit()
                else:
                    return make_response(jsonify({'error': 'GUID %s not found' % f}))

    ofiles = ['results.tgz']

    # Starts cloneReplica tasks
    ftasks = prepareInputFiles(container.id, site.se)

    # Saves output files meta
    for lfn in ofiles:
        file = File()
        file.scope = scope
        file.guid = getGUID(scope, lfn)
        file.type = 'output'
        file.lfn = lfn
        file.status = 'defined'
        db.session.add(file)
        db.session.commit()
        container.files.append(file)
        db.session.add(container)
        db.session.commit()

    # Counts files
    allfiles = container.files
    nifiles = 0
    nofiles = 0
    for f in allfiles:
        if f.type == 'input':
            nifiles += 1
        if f.type == 'output':
            nofiles += 1

    # Defines job meta
    job = Job()
    job.pandaid = None
    job.status = 'pending'
    job.owner = request.oauth.user
    job.params = params
    job.distr = distr
    job.container = container
    job.creation_time = datetime.utcnow()
    job.modification_time = datetime.utcnow()
    job.ninputfiles = nifiles
    job.noutputfiles = nofiles
    job.corecount = corecount
    job.tags = data['tags'] if 'tags' in data.keys() else ""
    db.session.add(job)
    db.session.commit()

    # Async sendjob
    res = chord(ftasks)(send_job.s(jobid=job.id, siteid=site.id))
    return make_response(jsonify({'id': job.id, 'container_id': guid}), 201)

@app.route('/api/job/<id>/info', methods=['GET'])
@oauth.require_oauth('api')
def jobStatusAPI(id):
    """Returns job status"""
    g.user = request.oauth.user

    n = Job.query.filter_by(id=id).count()
    if n == 0:
        data = {}
        data['status'] = 'Not found'
        return make_response(jsonify({'data': data}), 200)
    job = Job.query.filter_by(id=id).first()
    data = {}
    data['id'] = job.id
    data['panda_id'] = job.pandaid
    data['creation_time'] = str(job.creation_time)
    data['modification_time'] = str(job.modification_time)
    data['status'] = job.status
    return make_response(jsonify({'data': data}), 200)

@app.route('/api/job/<id>/logs', methods=['GET'])
@oauth.require_oauth('api')
def jobLogAPI(id):
    """Returns job stdout & stderr"""
    g.user = request.oauth.user

    job = Job.query.filter_by(id=id).one()
    extractLog(id)
    locdir = '/%s/.sys/%s' % (getScope(job.owner.username), job.container.guid)
    absdir = ddm_getlocalabspath(locdir)
    fout = find('payload.stdout', absdir)
    ferr = find('payload.stderr', absdir)
    out = ''
    err = ''
    if len(fout) > 0:
        with open(fout[0]) as f:
            out = f.read()
    if len(ferr) > 0:
        with open(ferr[0]) as f:
            err = f.read()
    data = {}
    data['id'] = id
    data['out'] = out
    data['err'] = err
    return make_response(jsonify({'data': data}), 200)

## PILOT ZONE

@app.route('/pilot/container', methods=['POST'])
def contNewAPI():
    """Saves new container"""
    cont = Container()
    guid = 'job.' + commands.getoutput('uuidgen')

    cont.guid = guid
    cont.status = 'open'
    db.session.add(cont)
    db.session.commit()

    url = '%s/%s' % (app.config['FTP'], guid)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], getScope(g.user.username), cont.guid))
    return make_response(jsonify({'ftp': url, 'guid': cont.guid}), 200)

@app.route('/pilot/container/<guid>/open', methods=['POST'])
def contOpenAPI(guid):
    """Changes container status to 'open'.
    :param guid: Container unique id
    """
    cont = Container.query.filter_by(guid=guid).first()
    cont.status = 'open'
    db.session.add(cont)
    db.session.commit()
    return make_response(jsonify({'response': 'Container status: open'}), 200)

@app.route('/pilot/container/<guid>/close', methods=['POST'])
def contCloseAPI(guid):
    """Changes container status to 'close'"""
    cont = Container.query.filter_by(guid=guid).first()

    path = os.path.join(app.config['UPLOAD_FOLDER'], getScope(g.user.username), cont.guid)
    os.path.walk(path, registerLocalFile, cont.guid)

    cont.status = 'close'
    db.session.add(cont)
    db.session.commit()
    return make_response(jsonify({'response': 'Container status: close'}), 200)

@app.route('/pilot/container/<guid>/info', methods=['GET'])
def contInfoAPI(guid):
    """Returns container metadata"""
    cont = Container.query.filter_by(guid=guid).first()
    data = {}
    data['id'] = cont.id
    data['guid'] = cont.guid
    data['status'] = cont.status
    data['nfiles'] = cont.files.count()
    return make_response(jsonify({'data': data}), 200)

@app.route('/pilot/file/<container_guid>/<lfn>/makereplica/<se>', methods=['POST'])
def makeReplicaAPI(container_guid, lfn, se):
    """Creates task to make new file replica"""
    nsite = Site.query.filter_by(se=se).count()
    if nsite == 0:
        return make_response(jsonify({'error': 'SE not found'}), 400)

    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = Container.query.filter_by(guid=container_guid).first()
    files = container.files
    for file in files:
        if file.lfn == lfn:
            rep_num = file.replicas.count()
            replicas = file.replicas
            if rep_num == 0:
                return make_response(jsonify({'status': 'Error: no replicas available'}), 500)

            ready_replica = None
            for r in replicas:
                if r.se == se:
                    return make_response(jsonify({'status': r.status}), 200)
                if r.se == app.config['DEFAULT_SE']:  # and r.status == 'ready'
                    ready_replica = r

            if ready_replica is None:
                ready_replica = replicas[0]

            task = cloneReplica.delay(ready_replica.id, se)
            return make_response(jsonify({'task_id': task.id}), 200)
    return make_response(jsonify({'error': 'File not found'}), 400)

@app.route('/pilot/file/<container_guid>/<lfn>/copy', methods=['POST'])
def stageinAPI(container_guid, lfn):
    """Creates task to copy file in path on se"""
    args = request.form
    if not ('to_se' in args.keys() and 'to_path' in args.keys()):
        return make_response(jsonify({'error': 'Please specify correct request params'}), 400)

    to_se = args.get('to_se', type=str)
    to_path = args.get('to_path', type=str)

    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = Container.query.filter_by(guid=container_guid).first()
    files = container.files
    for file in files:
        if file.lfn == lfn:
            rep_num = file.replicas.count()
            replicas = file.replicas

            for r in replicas:
                if r.status == 'ready':
                    task = copyReplica.delay(r.id, to_se, to_path)
                    return make_response(jsonify({'task_id': task.id}), 200)

            return make_response(jsonify({'status': 'Error: no replicas available'}), 204)
    return make_response(jsonify({'error': 'File not found'}), 400)

@app.route('/pilot/file/<container_guid>/<lfn>/info', methods=['GET'])
def pilotFileInfoAPI(container_guid, lfn):
    """Returns file metadata"""
    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = Container.query.filter_by(guid=container_guid).first()
    files = container.files
    for file in files:
        if file.lfn == lfn:
            data = {}
            data['lfn'] = file.lfn
            data['guid'] = file.guid
            data['modification_time'] = str(file.modification_time)
            data['fsize'] = int(file.fsize)
            data['adler32'] = file.checksum
            data['md5sum'] = file.md5sum
            return make_response(jsonify(data), 200)
    return make_response(jsonify({'error': 'File not found'}), 400)

@app.route('/pilot/file/<container_guid>/<lfn>/link', methods=['GET'])
def pilotFileLinkAPI(container_guid, lfn):
    """Returns ftp link to file"""
    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = Container.query.filter_by(guid=container_guid).first()
    site = Site.query.filter_by(se=app.config['DEFAULT_SE']).first()

    files = container.files
    for file in files:
        if file.lfn == lfn:
            replicas = file.replicas
            for r in replicas:
                if r.se == site.se and r.status == 'ready':
                    data = {}
                    data['lfn'] = file.lfn
                    data['guid'] = file.guid
                    data['ftp'] = getFtpLink(r.lfn)
                    return make_response(jsonify(data), 200)
    return make_response(jsonify({'error': 'File not found'}), 400)

@app.route('/pilot/file/<container_guid>/<lfn>/save', methods=['POST'])
def pilotFileSaveAPI(container_guid, lfn):
    """Saves file from request, returns file guid"""
    site = Site.query.filter_by(se=app.config['DEFAULT_SE']).first()

    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = Container.query.filter_by(guid=container_guid).first()
    if container.status != 'open':
        return make_response(jsonify({'error': 'Unable to upload: Container is not open'}), 400)
    files = container.files

    file = None
    for f in files:
        if f.lfn == lfn:
            file = f
    if not file:
        file = File()
        file.scope = getScope(g.user.username)
        file.type = 'input'
        file.lfn = lfn
        file.guid = getGUID(file.scope, file.lfn)
        file.status = 'defined'
        file.containers.append(container)
        db.session.add(file)
        db.session.commit()

    path = os.path.join(site.datadir, getScope(g.user.username), container.guid)
    replfn = '/' + os.path.join(getScope(g.user.username), container.guid, file.lfn)
    destination = os.path.join(path, file.lfn)

    for r in file.replicas:
        if r.se == site.se:
            destination = site.datadir + r.lfn
            file_dir = '/'.join(destination.split('/')[:-1])
            if r.status == 'ready':
                if os.path.isfile(destination): # Check fsize, md5 or adler
                    return make_response(jsonify({'error': 'Replica exists'}), 400)
                r.status == 'broken'
                db.session.add(r)
                db.session.commit()
                return make_response(jsonify({'error': 'Broken replica'}), 400)
            elif r.status == 'defined':
                try:
                    os.makedirs(file_dir)
                except(Exception):
                    pass
                f = open(destination, 'wb')
                f.write(request.data)
                f.close()

                # Update file info
                setFileMeta(file.id, destination)

                r.status = 'ready'
                db.session.add(r)
                db.session.commit()
                return make_response(jsonify({'guid': file.guid}), 200)
            else:
                return make_response(jsonify({'error': 'Replica status: %s' % r.status}), 400)


    replica = Replica()
    if os.path.isfile(destination):
        return make_response(jsonify({'error': 'Unable to upload: File exists'}), 400)
    try:
        os.makedirs(path)
    except(Exception):
        _logger.debug('Path exists: %s' % path)
    f = open(destination, 'wb')
    f.write(request.data)
    f.close()

    # Update file info
    setFileMeta(file.id, destination)

    # Create/change replica
    replica.se = site.se
    replica.status = 'ready'
    replica.lfn = replfn
    replica.token = ''
    replica.original = file
    db.session.add(replica)
    db.session.commit()
    return make_response(jsonify({'guid': file.guid}), 200)
    # return make_response(jsonify({'error': 'Illegal Content-Type'}), 400)

@app.route('/pilot/file/<container_guid>/<lfn>/fetch', methods=['GET'])
def pilotFileFetchAPI(container_guid, lfn):
    """Returns file in response"""

    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = Container.query.filter_by(guid=container_guid).first()
    files = container.files
    for file in files:
        if file.lfn == lfn:
            replicas = file.replicas
            for replica in replicas:
                if replica.se == app.config['DEFAULT_SE']:
                    fullpath = app.config['DATA_PATH'] + replica.lfn
                    f = open(fullpath, 'r')
                    rr = Response(f.read(), status=200, content_type='application/octet-stream')
                    rr.headers['Content-Disposition'] = 'inline; filename="%s"' % file.lfn
                    rr.headers['Content-MD5'] = file.md5sum
                    file.downloaded += 1
                    db.session.add(file)
                    db.session.commit()
                    return rr
    return make_response(jsonify({'error': 'File not found'}), 404)

@app.route('/pilot/task/<id>/info', methods=['GET'])
def taskStatusAPI(id):
    """Returns task status"""
    n = TaskMeta.query.filter_by(task_id=id).count()
    if n == 0:
        data = {}
        data['id'] = id
        data['status'] = 'unknown'
        data['date_done'] = ''
        data['traceback'] = ''
        return make_response(jsonify({'data': data}), 200)
    task = TaskMeta.query.filter_by(task_id=id).first()
    data = {}
    data['id'] = task.task_id
    data['status'] = task.status
    #data['results'] = str(task.result)
    data['date_done'] = str(task.date_done)
    data['traceback'] = task.traceback
    return make_response(jsonify({'data': data}), 200)