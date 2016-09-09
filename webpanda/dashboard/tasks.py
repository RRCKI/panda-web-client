# -*- coding: utf-8 -*-
from flask import Blueprint, request, render_template, current_app, session

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.dashboard import route_s


bp = Blueprint('tasks', __name__, url_prefix="/tasks")
_logger = NrckiLogger().getLogger("dashboard.tasks")


@route_s(bp, "/", methods=['GET'])
def list_all():
    hours_limit = request.args.get('hours', current_app.config['HOURS_LIMIT'], type=int)
    display_limit = request.args.get('display_limit', current_app.config['DISPLAY_LIMIT'], type=int)
    session['hours_limit'] = hours_limit
    session['display_limit'] = display_limit
    return render_template("dashboard/tasks/list.html")
