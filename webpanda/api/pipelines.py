# -*- coding: utf-8 -*-
from flask import Blueprint, g

from webpanda.api import route
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.services import pipelines_

bp = Blueprint('pipelines', __name__, url_prefix="/pipelines")
_logger = NrckiLogger().getLogger("api.pipelines")


@route(bp, "/", methods=['GET'])
def list_all():
    return pipelines_.find(owner_id=g.user.id).all()
