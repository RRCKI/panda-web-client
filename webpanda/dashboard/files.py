# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request, render_template, url_for, make_response, g, current_app, session, \
    Response
from webpanda.files import File
from webpanda.files.forms import NewFileForm
from werkzeug.utils import redirect

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.async.scripts import async_upload_dir
from webpanda.dashboard import route_s
from webpanda.services import files_, sites_
from webpanda.fc import scripts as fc


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
    scope = fc.getScope(user.username)
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
    Register files from HPC
    :return: Response obj
    """
    form = NewFileForm()
    if request.method == 'POST':
        path = form.path.data

        # Define SE connector
        se_name = 'RRC-KI-HPC'
        se = sites_.first(se=se_name)


        # Get container
        cont = fc.new_cont()

        # Upload files to container
        async_upload_dir.delay(cont.id, se.id, path)

        # Return container page
        return redirect(url_for('conts.cont_info', guid=cont.guid))

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
    if file.scope != fc.getScope(g.user.username):
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
