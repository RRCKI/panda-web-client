# -*- coding: utf-8 -*-
import os
import random
from app import app, db, lm
import commands
import json
from datetime import datetime
from flask import jsonify, request, make_response, g, Response
from flask_login import login_required
from scripts import registerLocalFile
from common.NrckiLogger import NrckiLogger
from common.utils import adler32, md5sum, fsize
from models import Distributive, Container, File, Site, Replica, TaskMeta
from ui.FileMaster import mqMakeReplica, makeReplica, cloneReplica, getGUID, getFtpLink, setFileMeta, copyReplica
from ui.FileMaster import getScope

_logger = NrckiLogger().getLogger("app.api")

@app.before_request
def before_requestAPI():
    _logger.debug(request.url)

@app.route('/api/sw', methods=['GET'])
@login_required
def swAPI():
    ds = Distributive.query.all()
    dlist = []
    for d in ds:
        a = {}
        a['id'] = d.id
        a['name'] = d.name
        a['version'] = d.version
        dlist.append(a)
    return make_response(jsonify({'data': dlist}), 200)

@app.route('/api/container', methods=['POST'])
def contNewAPI():
    """Returns list of available software"""
    cont = Container()
    guid = 'job.' + commands.getoutput('uuidgen')

    cont.guid = guid
    cont.status = 'open'
    db.session.add(cont)
    db.session.commit()

    url = '%s/%s' % (app.config['FTP'], guid)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], getScope(g.user.username), cont.guid))
    return make_response(jsonify({'ftp': url, 'guid': cont.guid}), 200)

@app.route('/api/container/<guid>/open', methods=['POST'])
def contOpenAPI(guid):
    """Changes container status to 'open'.
    :param guid: Container unique id
    """
    cont = Container.query.filter_by(guid=guid).first()
    cont.status = 'open'
    db.session.add(cont)
    db.session.commit()
    return make_response(jsonify({'response': 'Container status: open'}), 200)

@app.route('/api/container/<guid>/close', methods=['POST'])
def contCloseAPI(guid):
    """Changes container status to 'close'"""
    cont = Container.query.filter_by(guid=guid).first()

    path = os.path.join(app.config['UPLOAD_FOLDER'], getScope(g.user.username), cont.guid)
    os.path.walk(path, registerLocalFile, cont.guid)

    cont.status = 'close'
    db.session.add(cont)
    db.session.commit()
    return make_response(jsonify({'response': 'Container status: close'}), 200)

@app.route('/api/container/<guid>/info', methods=['GET'])
def contInfoAPI(guid):
    """Returns container metadata"""
    cont = Container.query.filter_by(guid=guid).first()
    data = {}
    data['id'] = cont.id
    data['guid'] = cont.guid
    data['status'] = cont.status
    data['nfiles'] = cont.files.count()
    return make_response(jsonify({'data': data}), 200)

@app.route('/api/container/<guid>/list', methods=['GET'])
def contListAPI(guid):
    """Returns list of files registered in container"""
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

@app.route('/api/file/<container_guid>/<lfn>/makereplica/<se>', methods=['POST'])
def makeReplicaAPI(container_guid, lfn, se):
    """Creates task to make new file replica"""
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

            replica = replicas[0] #TODO Update chosing method
            task = cloneReplica.delay(replica.id, se)

            task_obj = TaskMeta.query.filter_by(task_id=task.id).one()

            db.session.add(file)
            db.session.commit()
            return make_response(jsonify({'status': task_obj.status}), 200)
    return make_response(jsonify({'error': 'File not found'}), 400)

@app.route('/api/file/<container_guid>/<lfn>/copy', methods=['POST'])
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

@app.route('/api/file/<container_guid>/<lfn>/info', methods=['GET'])
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

@app.route('/api/file/<container_guid>/<lfn>/link', methods=['GET'])
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

@app.route('/api/file/<container_guid>/<lfn>/save', methods=['POST'])
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

@app.route('/api/file/<container_guid>/<lfn>/fetch', methods=['GET'])
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
                    file.downloaded += 1
                    db.session.add(file)
                    db.session.commit()
                    return rr
    return make_response(jsonify({'error': 'File not found'}), 400)

@app.route('/api/task/<id>/info', methods=['GET'])
def taskStatusAPI(id):
    """Returns task status"""
    task = TaskMeta.query.filter_by(task_id=id).first()
    data = {}
    data['id'] = task.task_it
    data['status'] = task.status
    data['results'] = str(task.result)
    data['date_done'] = str(task.date_done)
    data['traceback'] = task.traceback
    return make_response(jsonify({'data': data}), 200)

