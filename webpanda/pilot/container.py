# -*- coding: utf-8 -*-
import commands
from flask import jsonify, Blueprint, make_response, g, current_app
import os

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.core import WebpandaError
from webpanda.files import Container
from webpanda.files.scripts import getScope, registerLocalFile
from webpanda.pilot import route
from webpanda.services import conts_


bp = Blueprint('container', __name__, url_prefix="/container")
_logger = NrckiLogger().getLogger("pilot.container")


@route(bp, '/', methods=['POST'])
def new_cont():
    """Saves new container"""
    cont = Container()
    guid = 'job.' + commands.getoutput('uuidgen')

    cont.guid = guid
    cont.status = 'open'
    conts_.save(cont)

    url = '%s/%s' % (current_app.config['FTP'], guid)
    os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], getScope(g.user.username), cont.guid))
    return {'ftp': url, 'guid': cont.guid}


@route(bp, '/<guid>/open', methods=['POST'])
def cont_open(guid):
    """Changes container status to 'open'.
    :param guid: Container unique id
    """
    cont = conts_.first(guid=guid)
    if cont is None:
        raise WebpandaError("Container not found")

    cont.status = 'open'
    conts_.save(cont)
    return {'response': 'Container status: open'}


@route(bp, '/<guid>/close', methods=['POST'])
def cont_close(guid):
    """Changes container status to 'close'"""
    cont = conts_.first(guid=guid)
    if cont is None:
        raise WebpandaError("Container not found")

    path = os.path.join(current_app.config['UPLOAD_FOLDER'], getScope(g.user.username), cont.guid)
    os.path.walk(path, registerLocalFile, cont.guid)

    cont.status = 'close'
    conts_.save(cont)
    return {'response': 'Container status: close'}


@route(bp, '/<guid>/info', methods=['GET'])
def cont_info(guid):
    """Returns container metadata"""
    cont = conts_.first(guid=guid)
    if cont is None:
        raise WebpandaError("Container not found")

    data = dict()
    data['id'] = cont.id
    data['guid'] = cont.guid
    data['status'] = cont.status
    data['nfiles'] = len(cont.files)
    return data

