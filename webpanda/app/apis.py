# -*- coding: utf-8 -*-
import os
import random
from app import app, db, lm
import commands
import json
from flask import jsonify, request, make_response, g
from flask_login import login_required
from models import Distributive, Container, File
from ui.FileMaster import mqMakeReplica, makeReplica, cloneReplica


@app.route('/api/v0.1/sw', methods=['GET'])
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

@app.route('/api/v0.1/upload', methods=['POST'])
def upload1API():
    cont = Container()
    guid = commands.getoutput('uuidgen')

    cont.guid = guid
    db.session.add(cont)
    db.session.commit()
    return make_response(jsonify({'guid': guid}), 200)

@app.route('/api/v0.1/upload/<guid>', methods=['POST'])
def upload2API(guid):
    cont = Container.query.filter_by(guid = guid).first()

    if cont != None:
        content = request.data
        data = json.loads(content)
        for f in data['files']:
            file = File()
            file.scope = g.user.username
            file.guid = commands.getoutput('uuidgen')
            file.type = 'input'
            file.se = f['se']
            file.lfn = f['lfn']
            file.token = f['token']
            file.status = 'registered'
            db.session.add(file)
            db.session.commit()
            cont.files.append(file)
            db.session.add(cont)
            db.session.commit()

            # Create MQ request
            mqMakeReplica(file.id, app.config['DEFAULT_SE'])
        return make_response(jsonify({'status': 'Success'}), 200)

    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/api/v0.1/transfer/<guid>')
def transferStatusAPI(guid):
    file = File.query.filter_by(guid=guid).one()
    taskid = file.transfertask
    replicas = file.replicas
    if not replicas:
        return make_response(jsonify({'status': 'ERROR: File meta exists but no replicas available'}), 200)
    if taskid:
        task = cloneReplica.AsyncResult(taskid)
        status = task.status
        if status == 'FAILURE':
            replica = random.choice(replicas)
            task = cloneReplica(replica.id, 'local')
            file.transfertask = task.id
            db.session.add(file)
            db.session.commit()
            return make_response(jsonify({'oldstatus': status, 'status': task.status}), 200)

        if status == 'SUCCESS':
            url = '/'.join(app.config['HOSTNAME'], 'file', file.guid, file.lfn.split('/')[-1])
            return make_response(jsonify({'status': 'SUCCESS', 'url': url}), 200)
        return make_response(jsonify({'status': status}), 200)
    task = cloneReplica.s(replicas[0].id, 'local')
    status = task.status
    file.transfertask = task.id
    db.session.add(file)
    db.session.commit()
    return make_response(jsonify({'status': status}), 200)


