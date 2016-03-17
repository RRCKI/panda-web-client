# -*- coding: utf-8 -*-
from datetime import datetime
from flask import g, jsonify, Blueprint
from flask.ext.login import login_user, logout_user, current_user, login_required

from webpanda.app import route


bp = Blueprint('dashboard', __name__, template_folder='templates')


@bp.before_request
def before_request():
    g.user = current_user
    g.user.last_seen = datetime.utcnow()
    g.user.save()


@route(bp, '/help', methods=['GET'])
def help():
    return jsonify({'status': g.user.username}), 200
