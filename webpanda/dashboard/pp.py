# -*- coding: utf-8 -*-
import commands
from flask import Blueprint, jsonify, request, render_template, url_for, g, make_response, current_app, session
from webpanda.core import WebpandaError
from webpanda.files.forms import RunForm
from werkzeug.utils import redirect

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.dashboard import route_s
from webpanda.files import Container
from webpanda.services import conts_, pipeline_types_, files_, pipelines_, tasks_
from webpanda.tasks import Pipeline
from webpanda.tasks.forms import NewPipelineForm
from webpanda.fc import client as fc
from webpanda.pipelines import client as pclient


bp = Blueprint('pipelines', __name__, url_prefix="/pipelines")
_logger = NrckiLogger().getLogger("dashboard.pipelines")


@route_s(bp, "/", methods=['GET'])
def list_all():
    hours_limit = request.args.get('hours', current_app.config['HOURS_LIMIT'], type=int)
    display_limit = request.args.get('display_limit', current_app.config['DISPLAY_LIMIT'], type=int)
    session['hours_limit'] = hours_limit
    session['display_limit'] = display_limit
    return render_template("dashboard/pp/list.html")



@route_s(bp, "/<id>", methods=['GET'])
def pipeline_info(id):
    """
    Pipeline info view
    :param guid: guid of job
    :return: Response obj
    """
    pp = pipelines_.get(id)
    tasks = pclient.get_tasks(pp)
    return render_template("dashboard/pp/pp.html", pp=pp, tasks=tasks)


@route_s(bp, "/new", methods=['GET', 'POST'])
def new_pipeline():
    form = NewPipelineForm(request.form)

    if request.method == 'POST':
        ifiles = request.form.getlist('iguids[]')

        current_user = g.user

        # Prepare pipeline
        pp = Pipeline()
        pp.status = 'running'
        pp.type_id = pipeline_types_.get(1).id
        pp.owner_id = current_user.id
        pipelines_.save(pp)

        # Prepare container
        pp_cont = Container()
        pp_cont.guid = 'pipeline.' + commands.getoutput('uuidgen')
        conts_.save(pp_cont)

        # Add guids to container
        for item in ifiles:
            if item != '':
                f = files_.first(guid=item)
                if f is not None:
                        # Register file in catalog
                        fc.reg_file_in_cont(f, pp_cont, 'input')
                else:
                    pp_cont.status = 'broken'
                    conts_.save(pp_cont)
                    return make_response(jsonify({'error': "GUID {} not found".format(f)}))

        # Set current task
        start_task = pclient.get_start_task(pp)
        start_task.input = pp_cont.id
        start_task.output = pp_cont.id
        tasks_.save(start_task)

        return redirect(url_for('pipelines.list_all'))

    return render_template('dashboard/pp/new.html', form=form)


@route_s(bp, "/new/cont", methods=['GET', 'POST'])
def new_pipeline_from_cont():
    form = RunForm(request.form)

    if request.method == 'POST':
        icont = conts_.first(guid=form.guid.data)
        if icont is None:
            raise WebpandaError("Container not found")

        current_user = g.user

        # Prepare pipeline
        pp = Pipeline()
        pp.status = 'running'
        pp.type_id = pipeline_types_.get(1).id
        pp.owner_id = current_user.id
        pipelines_.save(pp)

        # Prepare container
        pp_cont = Container()
        pp_cont.guid = 'pipeline.' + commands.getoutput('uuidgen')
        conts_.save(pp_cont)

        # Add guids to container
        for item in icont.files:
            f = item.file
            # Register file in catalog
            fc.reg_file_in_cont(f, pp_cont, 'input')

        # Set current task
        start_task = pclient.get_start_task(pp)
        start_task.input = pp_cont.id
        start_task.output = pp_cont.id
        tasks_.save(start_task)

        return redirect(url_for('pipelines.list_all'))

    return render_template('dashboard/pp/new.html', form=form)