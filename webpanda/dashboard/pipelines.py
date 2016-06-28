# -*- coding: utf-8 -*-
import commands
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template, url_for, g, make_response
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.dashboard import route, route_s
from webpanda.files import Container
from webpanda.files.models import Catalog
from webpanda.services import pipelines_, conts_, tasks_, pipeline_types_, files_, catalog_
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
        ifiles = form.ifiles.data
        print ifiles

        current_user = g.user

        # Prepare pipeline
        pp = Pipeline()
        pp.status = 'running'
        pp.current_state = 'init_task'
        pp.type_id = pipeline_types_.get(1).id
        pp.owner_id = current_user.id

        # Prepare container
        pp_cont = Container()
        pp_cont.guid = 'pipeline.' + commands.getoutput('uuidgen')
        conts_.save(pp_cont)

        # Add guids to container
        for item in ifiles.split(';'):
            f = files_.first(guid=item)
            if f is not None:
                    # Add file to container
                    cc = Catalog()
                    cc.file = f
                    cc.cont = pp_cont
                    cc.type = 'input'
                    catalog_.save(cc)
            else:
                pp_cont.status = 'broken'
                conts_.save(pp_cont)
                return make_response(jsonify({'error': "GUID {} not found".format(f)}))

        # Prepare init task
        task = Task()
        task.owner_id = current_user.id
        task.task_type_id = 2
        task.creation_time = datetime.utcnow()
        task.modification_time = datetime.utcnow()
        task.status = 'defined'
        task.input = pp_cont.id
        task.output = pp_cont.id
        tasks_.save(task)

        pp.init_task_id = task.id
        pipelines_.save(pp)

        return redirect(url_for('pipelines.list_all'))

    return render_template('dashboard/pp/new.html', form=form)
