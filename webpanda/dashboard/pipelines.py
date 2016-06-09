# -*- coding: utf-8 -*-
import commands
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template, url_for
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.dashboard import route, route_s
from webpanda.files import Container
from webpanda.services import pipelines_, conts_
from webpanda.tasks import Pipeline, Task
from webpanda.tasks.forms import NewPipelineForm
from werkzeug.utils import redirect

bp = Blueprint('pipelines', __name__, url_prefix="/pipelines")
_logger = NrckiLogger().getLogger("dashboard.pipelines")


@route_s(bp, "/start", methods=['GET'])
def start():
    # Add your code here
    return jsonify(status='success'), 200


@route_s(bp, "/", methods=['GET'])
def list_all():
    # Add your code here
    return jsonify(status='success'), 200


@route_s(bp, "/new", methods=['GET', 'POST'])
def new_pipeline():
    form = NewPipelineForm(request.form)

    if request.method == 'POST' and form.validate():
        ifiles = form.ifiles

        # Prepare pipeline
        pp = Pipeline()
        pp.current_state = 'init'
        pp.type = pipelines_.get(1)

        # Prepare container
        pp_cont = Container()
        pp_cont.guid = 'pipeline.' + commands.getoutput('uuidgen')
        conts_.save(pp_cont)

        # Prepare init task
        task = Task()
        task.owner_id = 1
        task.task_type_id = 2
        task.tag = "paleomix"
        task.creation_time = datetime.utcnow()
        task.modification_time = datetime.utcnow()
        task.status = 'defined'
        task.ifiles = pp_cont.guid
        task.ofiles = pp_cont.guid

        return redirect(url_for('pipelines.list_all'))

    return render_template('dashboard/pp/new.html', form=form)
