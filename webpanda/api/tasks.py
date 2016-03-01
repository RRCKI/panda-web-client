# -*- coding: utf-8 -*-
from flask import render_template, jsonify, Blueprint

from webpanda.api import route
from webpanda.services import tasks as _tasks
from webpanda.services import jobs as _jobs
from webpanda.common.NrckiLogger import NrckiLogger


bp = Blueprint('tasks', __name__, url_prefix="/tasks")
_logger = NrckiLogger().getLogger("api.tasks")


@route(bp, "/<tag>", methods=['GET'])
def show(tag):
    return _tasks.first(tag=tag)


@route(bp, "/<tag>/jobs", methods=['GET'])
def show_jobs(tag):
    task = _tasks.first(tag=tag)
    return task.jobs