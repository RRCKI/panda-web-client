# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request, render_template, url_for
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.dashboard import route, route_s
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
        # Add your code here
        print "Add your code here"

        return redirect(url_for('pipelines.list_all'))

    return render_template('dashboard/pp/new.html', form=form)
