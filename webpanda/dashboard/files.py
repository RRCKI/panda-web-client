# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request, render_template, url_for, make_response, g, current_app, session, \
    Response
from webpanda.files import File, Replica
from webpanda.files.forms import NewFileForm
from werkzeug.utils import redirect

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.async.scripts import async_cloneReplica
from webpanda.dashboard import route_s
from webpanda.files.scripts import getScope, getUrlInfo, getGUID
from webpanda.services import conts_, files_, replicas_, sites_
from webpanda.core import fc


bp = Blueprint('files', __name__, url_prefix="/files")
_logger = NrckiLogger().getLogger("dashboard.files")


@route_s(bp, "/", methods=['GET'])
def files():
    """
    List of user's files view
    :return: Response obj
    """
    hours_limit = request.args.get('hours', current_app.config['HOURS_LIMIT'], type=int)
    display_limit = request.args.get('display_limit', current_app.config['DISPLAY_LIMIT'], type=int)
    session['hours_limit'] = hours_limit
    session['display_limit'] = display_limit
    return render_template("dashboard/files/file_list.html")


@route_s(bp, "/list", methods=['GET'])
def files_list():
    """
    Get list of files method for ajax
    :return: List of File obj
    """
    user = g.user

    hours_limit = session.get('hours_limit', current_app.config['HOURS_LIMIT'])
    display_limit = session.get('display_limit', current_app.config['DISPLAY_LIMIT'])
    scope = getScope(user.username)
    # show users jobs
    files = files_.find(scope=scope).order_by(File.id).limit(display_limit)

    # prepare json
    files_o = []
    for file in files:
        file_o = {}
        file_o['id'] = file.id
        file_o['scope'] = file.scope
        file_o['guid'] = file.guid
        file_o['type'] = file.type
        file_o['lfn'] = file.lfn
        file_o['status'] = file.status
        files_o.append(file_o)
    data = {}
    data['data'] = files_o

    return make_response(jsonify(data), 200)


@route_s(bp, "/<guid>", methods=['GET'])
def file_info(guid):
    """
    File info view
    :param guid: guid of file
    :return: Response obj
    """
    try:
        file = files_.first(guid=guid)
    except(Exception):
        _logger.error(Exception.message)
        return 'File not found'
    return render_template("dashboard/files/file.html", file=file, replicas=file.replicas)


@route_s(bp, "/new", methods=['GET', 'POST'])
def index():
    """
    New file form view
    :return: Response obj
    """
    form = NewFileForm()
    if request.method == 'POST':
        se = form.se.data

        from_se, path, token = getUrlInfo(form.url.data)

        file = File()
        file.scope = getScope(g.user.username)
        file.lfn = path.split('/')[-1]
        file.guid = getGUID(file.scope, file.lfn)
        file.status = 'defined'
        files_.save(file)
        cont_guid = form.container.data

        if (cont_guid not in [None, '']): # TODO Check regex
            container = conts_.first(guid=cont_guid)
            # Register file in catalog
            fc.reg_file_in_cont(file, container, 'input')


        replica = Replica()
        replica.se = from_se
        replica.status = 'ready'
        replica.token = token
        replica.lfn = ':/'.join([from_se, path])
        replica.original = file
        replicas_.save(replica)

        resp = async_cloneReplica.delay(replica.id, se)
        return redirect(url_for('file_info', guid=file.guid))

    form.se.choices = [("%s" % site.se, "%s" % site.se) for site in sites_.find(active=1)]
    return render_template("dashboard/files/file_new.html", form=form)


@route_s(bp, "/<guid>/download", methods=['GET'])
def file_download(guid):
    """
    Get file as stream
    :param guid: guid of file
    :return: Response obj
    """
    try:
        file = files_.first(guid=guid)
    except(Exception):
        _logger.error(Exception.message)
        return make_response(jsonify({'error': 'File not found'}), 404)
    if file.scope != getScope(g.user.username):
        return make_response(jsonify({'error': 'File is not in your scope'}), 403)

    replicas = file.replicas
    for replica in replicas:
        if replica.se == current_app.config['DEFAULT_SE'] and replica.status == 'ready':
            fullpath = current_app.config['DATA_PATH'] + replica.lfn
            f = open(fullpath, 'r')
            rr = Response(f.read(), status=200, content_type='application/octet-stream')
            rr.headers['Content-Disposition'] = 'inline; filename="%s"' % file.lfn
            rr.headers['Content-MD5'] = file.md5sum
            file.downloaded += 1
            files_.save(file)
            return rr
    return make_response(jsonify({'error': 'No ready replica'}), 404)
