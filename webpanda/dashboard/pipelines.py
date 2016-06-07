# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, current_app, request, session, jsonify
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.dashboard import route

bp = Blueprint('pipelines', __name__, url_prefix="/pipelines")
_logger = NrckiLogger().getLogger("dashboard.pipelines")


@route(bp, "/start", methods=['GET'])
def start():
    # Add your code here
    return jsonify(status='success'), 200
