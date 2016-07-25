import commands
from flask import Blueprint, g, request, make_response, jsonify, session, render_template, url_for, current_app
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.dashboard import route_s
from webpanda.files import Container
from webpanda.files.forms import NewContainerForm
from webpanda.files.scripts import getScope
from webpanda.services import conts_
from webpanda.async.scripts import async_uploadContainer
from werkzeug.utils import redirect

bp = Blueprint('conts', __name__, url_prefix="/cont")
_logger = NrckiLogger().getLogger("dashboard.conts")


@route_s(bp, "/", methods=['GET'])
def containers():
    """
    List of user's containers view
    :return: Response obj
    """
    hours_limit = request.args.get('hours', current_app.config['HOURS_LIMIT'], type=int)
    display_limit = request.args.get('display_limit', current_app.config['DISPLAY_LIMIT'], type=int)
    session['hours_limit'] = hours_limit
    session['display_limit'] = display_limit
    return render_template("dashboard/cont/cont_list.html")


@route_s(bp, "/list", methods=['GET'])
def conts_list():
    """
    Get list of containers method for ajax
    :return: List of Container obj
    """
    user = g.user

    hours_limit = session.get('hours_limit', current_app.config['HOURS_LIMIT'])
    display_limit = session.get('display_limit', current_app.config['DISPLAY_LIMIT'])
    scope = getScope(user.username)
    # show users jobs
    conts = conts_.find(status='user').order_by(Container.id.desc()).limit(30)

    # prepare json
    conts_o = []
    for cont in conts:
        cont_o = {}
        cont_o['id'] = cont.id
        cont_o['guid'] = cont.guid
        cont_o['status'] = cont.status
        cont_o['n'] = len(cont.files)
        conts_o.append(cont_o)
    data = {}
    data['data'] = conts_o

    return make_response(jsonify(data), 200)


@route_s(bp, "/<guid>", methods=['GET'])
def cont_info(guid):
    """
    Container info view
    :param guid: guid of container
    :return: Response obj
    """
    try:
        container = Container.query.filter_by(guid=guid).one()
    except(Exception):
        _logger.error(Exception.message)
        return make_response(jsonify({'message': 'Container not found'}), 404)
    return render_template("dashboard/cont/cont.html", cont=container, files=container.files)


@route_s(bp, "/new", methods=['GET', 'POST'])
def container():
    """
    New container form view
    :return: Response obj
    """
    form = NewContainerForm()
    if request.method == 'POST':
        user = g.user
        scope = getScope(user.username)

        ftpdir = form.ftpdir.data

        #Create a unique container quid for this particular batch of uploads.
        cguid = 'job.' + commands.getoutput('uuidgen')

        # Create new container
        container = Container()
        container.guid = cguid
        container.status = 'open'
        conts_.save(container)

        # Check if ftpdir empty
        if ftpdir and len(ftpdir) > 0:
            async_uploadContainer.delay(ftpdir, scope, container.guid)

        return redirect(url_for('cont.cont_info', guid=container.guid))

    return render_template("dashboard/cont/cont_new.html", form=form)

