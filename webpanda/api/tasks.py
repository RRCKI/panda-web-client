# -*- coding: utf-8 -*-
from flask import render_template, jsonify, Blueprint

from webpanda.api import route
from webpanda.services import tasks_
from webpanda.common.NrckiLogger import NrckiLogger


bp = Blueprint('tasks', __name__, url_prefix="/tasks")
_logger = NrckiLogger().getLogger("api.tasks")


@route(bp, "/", methods=['GET'])
def list_all():
    return tasks_.all()


@route(bp, "/<tag>", methods=['GET'])
def show(tag):
    return tasks_.first(tag=tag)


@route(bp, "/<tag>/jobs", methods=['GET'])
def show_jobs(tag):
    task = tasks_.first(tag=tag)
    return task.jobs