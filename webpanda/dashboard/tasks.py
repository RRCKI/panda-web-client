# -*- coding: utf-8 -*-
from flask import Blueprint, request, render_template, current_app, session, jsonify
from flask import g
from flask import make_response

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.dashboard import route_s
from webpanda.services import tasks_, jobs_
from webpanda.tasks import Task

bp = Blueprint('tasks', __name__, url_prefix="/tasks")
_logger = NrckiLogger().getLogger("dashboard.tasks")


@route_s(bp, "/", methods=['GET'])
def list_all():
    hours_limit = request.args.get('hours', current_app.config['HOURS_LIMIT'], type=int)
    display_limit = request.args.get('display_limit', current_app.config['DISPLAY_LIMIT'], type=int)
    session['hours_limit'] = hours_limit
    session['display_limit'] = display_limit
    return render_template("dashboard/tasks/list.html")


@route_s(bp, "/<id>", methods=['GET'])
def task_info(id):
    """
    Task info view
    :param guid: guid of job
    :return: Response obj
    """
    task = tasks_.get(id)
    jobs = jobs_.find(tags=task.tag)
    return render_template("dashboard/tasks/task.html", jobs=jobs, task=task)


@route_s(bp, "/list", methods=['GET'])
def tasks_list():
    """
    Get list of jobs method for ajax
    :return: List of Job obj
    """
    user = g.user

    # show users jobs
    tasks = tasks_.find(owner_id=user.id).order_by(Task.id.desc()).all()

    return make_response(jsonify({"data": tasks}), 200)
