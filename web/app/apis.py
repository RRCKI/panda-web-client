# -*- coding: utf-8 -*-
from app import app, db, lm
from flask import jsonify, request
from models import Distributive


@app.route('/api/sw')
def swAPI():
    if request.method == 'GET':
        ds = Distributive.query.all()
        dlist = []
        for d in ds:
            a = {}
            a['id'] = d.id
            a['name'] = d.name
            a['version'] = d.version
            dlist.append(a)
        return jsonify({'data': dlist})
    return

