# -*- coding: utf-8 -*-
from flask import jsonify, Blueprint, make_response

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.pilot import route
from webpanda.services import transfers_meta_


bp = Blueprint('task', __name__, url_prefix="/task")
_logger = NrckiLogger().getLogger("pilot.task")

@route(bp, '/<id>/info', methods=['GET'])
def task_info(id):
    """Returns task status"""
    n = transfers_meta_.find(task_id=id).count()
    if n == 0:
        data = {}
        data['id'] = id
        data['status'] = 'unknown'
        data['date_done'] = ''
        data['traceback'] = ''
        return data

    task = transfers_meta_.first(task_id=id)
    data = {}
    data['id'] = task.task_id
    data['status'] = task.status
    #data['results'] = str(task.result)
    data['date_done'] = str(task.date_done)
    data['traceback'] = task.traceback
    return data