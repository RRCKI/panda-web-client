# -*- coding: utf-8 -*-
from flask import render_template, jsonify, Blueprint

from webpanda.api import route
from webpanda.services import jobs as _jobs
from webpanda.common.NrckiLogger import NrckiLogger


bp = Blueprint('jobs', __name__, url_prefix="/jobs")
_logger = NrckiLogger().getLogger("api.jobs")


@route(bp, "/<id_>", methods=['GET'])
def show(id_):
    return _jobs.get(id_)

@route(bp, "/tag/<tag>", methods=['GET'])
def bytag(tag):
    return _jobs.find(tags=tag).all()
