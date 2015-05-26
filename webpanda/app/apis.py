# -*- coding: utf-8 -*-
from app import app, db, lm
import commands
import json
from flask import jsonify, request, make_response, g
from flask_login import login_required
from models import Distributive, Container, File


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
    return jsonify({'data': dlist})

@app.route('/api/v0.1/upload', methods=['POST'])
def upload1API():
    cont = Container()
    guid = commands.getoutput('uuidgen')

    cont.guid = guid
    db.session.add(cont)
    db.session.commit()
    return make_response(jsonify({'guid': guid}), 200)

@app.route('/api/v0.1/upload/<guid>', methods=['POST'])
@login_required
def upload2API(guid):
    cont = Container.query.filter_by(guid = guid).first()

    if cont != None:
        from mq.MQ import MQ
        routing_key = app.config['MQ_FILEKEY']
        mq = MQ(host=app.config['MQ_HOST'], exchange=app.config['MQ_EXCHANGE'])

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
            data = {}
            data['fileid'] = file.id
            data['params'] = {'dir': cont.guid}
            data['se'] = app.config['DEFAULT_SE']
            message = json.dumps(data)
            print 'mq.sendMessage(message, routing_key)'
            print message
            #mq.sendMessage(message, routing_key)
        return make_response(jsonify({'status': 'Success'}), 200)

    return make_response(jsonify({'error': 'Not found'}), 404)


