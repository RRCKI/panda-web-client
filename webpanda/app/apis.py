# -*- coding: utf-8 -*-
import os
import random
from app import app, db, lm
import commands
import json
from datetime import datetime
from flask import jsonify, request, make_response, g, Response
from flask_login import login_required
from common.NrckiLogger import NrckiLogger
from common.utils import adler32, md5sum, fsize
from models import Distributive, Container, File, Site, TransferTask, Replica
from ui.FileMaster import mqMakeReplica, makeReplica, cloneReplica, getGUID, getFtpLink
from ui.FileMaster import getScope

_logger = NrckiLogger().getLogger("app.api")


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
    cont = Container.query.filter_by(guid=guid).first()
    cont.status = 'open'
    db.session.add(cont)
    db.session.commit()
    return make_response(jsonify({'response': 'Container status: open'}), 200)

@app.route('/api/container/<guid>/close', methods=['POST'])
def contCloseAPI(guid):
    cont = Container.query.filter_by(guid=guid).first()

    path = os.path.join(app.config['UPLOAD_FOLDER'], getScope(g.user.username), cont.guid)
    os.path.walk(path, registerLocalFile, cont.guid)

    cont.status = 'close'
    db.session.add(cont)
    db.session.commit()
    return make_response(jsonify({'response': 'Container status: close'}), 200)

@app.route('/api/container/<guid>/info', methods=['GET'])
def contInfoAPI(guid):
    cont = Container.query.filter_by(guid=guid).first()
    data = {}
    data['id'] = cont.id
    data['guid'] = cont.guid
    data['status'] = cont.status
    data['nfiles'] = cont.files.count()
    return make_response(jsonify({'data': data}), 200)

@app.route('/api/container/<guid>/list', methods=['GET'])
def contListAPI(guid):
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
        datalist.append(data)
    return make_response(jsonify({'data': datalist}), 200)

@app.route('/api/file/<dataset>/<lfn>/makereplica/<se>', methods=['POST'])
def makeReplicaAPI(dataset, lfn, se):
    if ':' in dataset:
        dataset = dataset.split(':')[-1]
    container = Container.query.filter_by(guid=dataset).first()
    files = container.files
    for file in files:
        if file.lfn == lfn:
            rep_num = file.replicas.count()
            replicas = file.replicas
            if rep_num == 0:
                return make_response(jsonify({'status': 'Error: no replicas available'}), 500)

            replica = replicas[0]
            task = cloneReplica.delay(replica.id, se)

            transfertask = TransferTask()
            transfertask.replica_id = replica.id
            transfertask.se = se
            transfertask.task_id = task.id
            transfertask.task_status = task.status

            db.session.add(file)
            db.session.commit()
            return make_response(jsonify({'status': transfertask.task_status}), 200)
    return make_response(jsonify({'error': 'File not found'}), 400)

@app.route('/api/file/<dataset>/<lfn>/info', methods=['GET'])
def pilotFileInfoAPI(dataset, lfn):
    if ':' in dataset:
        dataset = dataset.split(':')[-1]
    container = Container.query.filter_by(guid=dataset).first()
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

@app.route('/api/file/<dataset>/<lfn>/link', methods=['GET'])
def pilotFileLinkAPI(dataset, lfn):
    if ':' in dataset:
        dataset = dataset.split(':')[-1]
    container = Container.query.filter_by(guid=dataset).first()
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

@app.route('/api/file/<dataset>/<lfn>/save', methods=['POST'])
def pilotFileSaveAPI(dataset, lfn):
    if ':' in dataset:
        dataset = dataset.split(':')[-1]
    container = Container.query.filter_by(guid=dataset).first()
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

    site = Site.query.filter_by(se=app.config['DEFAULT_SE']).first()
    path = os.path.join(app.config['UPLOAD_FOLDER'], getScope(g.user.username), container.guid)
    dest = os.path.join(path, file.lfn)
    replica = None
    for r in file.replicas:
        if r.se == site.se and r.status == 'ready':
            if os.path.isfile(dest): # Check fsize, md5 or adler
                return make_response(jsonify({'error': 'Replica exists'}), 400)
            replica = r
    if not replica:
        replica = Replica()
        if os.path.isfile(dest):
            return make_response(jsonify({'error': 'Unable to upload: File exists'}), 400)
    if request.headers['Content-Type'] == 'application/octet-stream':
        try:
            os.makedirs(path)
        except(Exception):
            _logger.debug('Path exists: %s' % path)
        f = open(dest, 'wb')
        f.write(request.data)
        f.close()

        # Update file info
        file.checksum = adler32(dest)
        file.md5sum = md5sum(dest)
        file.fsize = fsize(dest)
        file.modification_time = datetime.utcnow()
        db.session.add(file)
        db.session.commit()

        # Create/change replica
        replica.se = site.se
        replica.status = 'ready'
        replica.lfn = dest
        replica.token = ''
        replica.original = file
        db.session.add(replica)
        db.session.commit()
        return make_response(jsonify({'guid': file.guid}), 200)
    return make_response(jsonify({'error': 'Illegal Content-Type'}), 400)

@app.route('/api/file/<dataset>/<lfn>/fetch', methods=['GET'])
def pilotFileFetchAPI(dataset, lfn):
    if ':' in dataset:
        dataset = dataset.split(':')[-1]
    container = Container.query.filter_by(guid=dataset).first()
    files = container.files
    for file in files:
        if file.lfn == lfn:
            replicas = file.replicas
            for replica in replicas:
                if replica.se == app.config['DEFAULT_SE']:
                    f = open(replica.lfn, 'r')
                    rr = Response(f.read(), status=200, content_type='application/octet-stream')
                    return rr
    return make_response(jsonify({'error': 'File not found'}), 400)

def registerLocalFile(arg, dirname, names):
    site = Site.query.filter_by(se=app.config['DEFAULT_SE']).first()
    _logger.debug(str(arg))
    cont = Container.query.filter_by(guid=arg).first()
    files = cont.files

    for name in names:
        fpath = os.path.join(dirname, name)

        fobj = None
        for file in files:
            if file.lfn == name:
                fobj = file
        if not fobj:
            fobj = File()
            fobj.scope = getScope(g.user.username)
            fobj.lfn = name
            fobj.guid = getGUID(fobj.scope, fobj.lfn)
            fobj.type = 'input'
            fobj.status = 'defined'
            fobj.checksum = adler32(fpath)
            fobj.md5sum = md5sum(fpath)
            fobj.fsize = fsize(fpath)
            fobj.modification_time = datetime.utcnow()
            fobj.containers.append(cont)
            db.session.add(fobj)
            db.session.commit()

        replicas = fobj.replicas
        replica = None
        for r in replicas:
            if r.se == site.se and r.status == 'ready':
                pass
        if not replica:
            replica = Replica()
            replica.se = site.se
            replica.status = 'ready'
            replica.token = ''
            replica.lfn = fpath
            replica.original = fobj
            db.session.add(replica)
            db.session.commit()