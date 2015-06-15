# -*- coding: utf-8 -*-
import os
import random
from app import app, db, lm
import commands
import json
from flask import jsonify, request, make_response, g
from flask_login import login_required
from models import Distributive, Container, File, Site
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

@app.route('/api/container', methods=['POST'])
def upload1API():
    cont = Container()
    guid = commands.getoutput('uuidgen')

    cont.guid = guid
    db.session.add(cont)
    db.session.commit()
    return make_response(jsonify({'guid': guid}), 200)

@app.route('/api/file', methods=['POST'])
def upload2API():
    site = Site.query.filter_by(ce=app.config['DEFAULT_CE']).first()

    content = request.data
    data = json.loads(content)
    isOK = True
    for f in data['files']:
        cont = Container.query.filter_by(guid=f['container']).first()
        if not cont:
            isOK = False
            continue
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
        task = makeReplica.delay(file.id, site.se)

    if isOK:
        return make_response(jsonify({'status': 'Success'}), 200)
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/api/file/<guid>/makereplica/<se>', methods=['POST'])
def makeReplicaAPI(guid, se):
    file = File.query.filter_by(guid=guid).first()
    taskid = file.transfertask
    rep_num = file.replicas.count()
    replicas = file.replicas
    if rep_num == 0:
        task = makeReplica.delay(file.id, se)
        file.transfertask = task.id
        db.session.add(file)
        db.session.commit()
        return make_response(jsonify({'status': task.status}), 200)
    if taskid:
        task = cloneReplica.AsyncResult(taskid)
        status = task.status
        if status == 'FAILURE':
            replica = random.choice(replicas)
            task = cloneReplica.delay(replica.id, se)
            file.transfertask = task.id
            db.session.add(file)
            db.session.commit()
            return make_response(jsonify({'oldstatus': status, 'status': task.status}), 200)

        if status == 'SUCCESS':
            url = '/'.join(app.config['HOSTNAME'], 'file', file.guid, file.lfn.split('/')[-1])
            return make_response(jsonify({'status': 'SUCCESS', 'url': url}), 200)
        return make_response(jsonify({'status': status}), 200)
    task = cloneReplica.delay(replicas[0].id, se)
    status = task.status
    file.transfertask = task.id
    db.session.add(file)
    db.session.commit()
    return make_response(jsonify({'status': status}), 200)


