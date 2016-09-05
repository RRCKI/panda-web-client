# -*- coding: utf-8 -*-
import commands
from flask import jsonify, Blueprint, make_response, g, current_app
import os

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.core import WebpandaError
from webpanda.files import Container
from webpanda.files.scripts import registerLocalFile
from webpanda.files.common import getScope
from webpanda.pilot import route
from webpanda.services import conts_


bp = Blueprint('container', __name__, url_prefix="/container")
_logger = NrckiLogger().getLogger("pilot.container")


@route(bp, '/', methods=['POST'])
def new_cont():
    """
    POST: /pilot/container

    Saves new container

    :return: ftp/guid
    :rtype: json
    """
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
    """
    POST: /pilot/container/<guid>/open

    Changes container status to 'open'.

    :param guid: Container guid
    :type guid: str
    """
    cont = conts_.first(guid=guid)
    if cont is None:
        raise WebpandaError("Container not found")

    cont.status = 'open'
    conts_.save(cont)
    return {'response': 'Container status: open'}


@route(bp, '/<guid>/close', methods=['POST'])
def cont_close(guid):
    """
    POST: /pilot/container/<guid>/close

    Changes container status to 'close'

    :param guid: Container guid
    :type guid: str
    """
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
    """
    POST: /pilot/container/<guid>/info

    Returns container metadata
    :param guid: Container guid
    :type guid: str
    :return: id/guid/status/nfiles
    :rtype: json
    """
    cont = conts_.first(guid=guid)
    if cont is None:
        raise WebpandaError("Container not found")

    data = dict()
    data['id'] = cont.id
    data['guid'] = cont.guid
    data['status'] = cont.status
    data['nfiles'] = len(cont.files)
    return data

