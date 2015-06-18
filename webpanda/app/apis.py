# -*- coding: utf-8 -*-
import os
import random
from app import app, db, lm
import commands
import json
from flask import jsonify, request, make_response, g, Response
from flask_login import login_required
from models import Distributive, Container, File, Site, TransferTask
from ui.FileMaster import mqMakeReplica, makeReplica, cloneReplica
from ui.FileMaster import getScope


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
def upload1API():
    cont = Container()
    guid = commands.getoutput('uuidgen')

    cont.guid = guid
    db.session.add(cont)
    db.session.commit()
    return make_response(jsonify({'guid': guid}), 200)

@app.route('/api/file/<guid>/makereplica/<se>', methods=['POST'])
def makeReplicaAPI(guid, se):
    file = File.query.filter_by(guid=guid).first()
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

@app.route('/api/file/<dataset>/<lfn>/info', methods=['GET'])
@login_required
def pilotFileChecksumAPI(dataset, lfn):
    if ':' in dataset:
        dataset = dataset.split(':')[-1]
    container = Container.query.filter_by(guid=dataset).fisrt()
    files = container.files
    for file in files:
        if file.lfn == lfn:
            data = {}
            data['modification_time'] = str(file.modification_time)
            data['fsize'] = int(file.fsize)
            data['adler32'] = file.checksum
            data['md5sum'] = file.md5sum
            return make_response(jsonify(data), 200)
    return make_response(jsonify({'error': 'File not found'}), 400)

@app.route('/api/file/<dataset>/<lfn>/save', methods=['POST'])
def pilotFileSaveAPI(dataset, lfn):
    if ':' in dataset:
        dataset = dataset.split(':')[-1]
    container = Container.query.filter_by(guid=dataset).first()
    files = container.files
    for file in files:
        if file.lfn == lfn:
            path = os.path.join(app.config['UPLOAD_FOLDER'], getScope(g.user.username), file.guid)
            dest = os.path.join(path, file.lfn)
            if os.path.isfile(path):
                return make_response(jsonify({'error': 'File exists'}), 400)
            if request.headers['Content-Type'] == 'application/octet-stream':
                os.makedirs(path)
                f = open(dest, 'wb')
                f.write(request.data)
                f.close()
                return make_response(jsonify({'guid': file.guid}), 200)
    return make_response(jsonify({'error': 'File meta not found'}), 400)

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
