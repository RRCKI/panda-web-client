import commands
import json
from flask import render_template, Blueprint, g, request, url_for, current_app
import os
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.common.utils import adler32, md5sum, fsize
from webpanda.dashboard import route_s
from webpanda.ddm.scripts import ddm_checkifexists
from webpanda.files import Container, File, Replica
from webpanda.files.scripts import getScope, setFileMeta
from webpanda.files.scripts import getGUID
from webpanda.services import sites_, conts_, files_, replicas_
from werkzeug.utils import redirect
from webpanda.fc.Client import Client as fc

bp = Blueprint('main', __name__)
_logger = NrckiLogger().getLogger("dashboard.main")

@route_s(bp, '/')
def index():
    user = g.user
    return render_template("dashboard/main/index.html",
        title = 'Home',
        user = user)


@route_s(bp, '/help')
def help():
    return render_template("dashboard/main/help.html")

@route_s(bp, "/upload", methods=['POST'])
def upload():
    form = request.form

    # Create a unique container quid for this particular batch of uploads.
    cguid = 'job.' + commands.getoutput('uuidgen')

    # Is the upload using Ajax, or a direct POST by the form?
    is_ajax = False
    if form.get("__ajax", None) == "true":
        is_ajax = True

    # Create new container
    container = Container()
    container.guid = cguid
    container.status = 'open'
    conts_.save(container)

    # Process files in request
    for upload in request.files.getlist("file"):
        # Define file params
        lfn = upload.filename.rsplit("/")[0]
        scope = getScope(g.user.username)
        guid = getGUID(scope, lfn)
        site = sites_.first(se=current_app.config['DEFAULT_SE'])

        # Target folder for these uploads.
        dir = '/' + os.path.join('system', scope, guid)
        target = site.datadir + dir
        try:
            os.makedirs(target)
        except:
            if is_ajax:
                return ajax_response(False, "Couldn't create upload directory: %s" % target)
            else:
                return "Couldn't create upload directory: %s" % target

        replfn = os.path.join(dir, lfn)
        destination = os.path.join(target, lfn)
        upload.save(destination)

        if os.path.isfile(destination):
            # Check file existence in catalog
            adler = adler32(destination)
            md5 = md5sum(destination)
            size = fsize(destination)
            file_id = ddm_checkifexists(lfn, size, adler, md5)

            if file_id:
                # If file exists
                file = files_.get(file_id)
            else:
                # Otherwise create new
                file = File()
                file.scope = scope
                file.guid = guid
                file.type = 'input'
                file.lfn = lfn
                file.token = ''
                file.status = 'defined'
                files_.save(file)
                setFileMeta(file.id, destination)

                replica = Replica()
                replica.se = site.se
                replica.status = 'ready'
                replica.lfn = replfn
                replica.original = file
                replicas_.save(replica)

            # Register file in container
            fc.reg_file_in_cont(file, container, 'input')

        else:
            return ajax_response(False, "Couldn't save file: %s" % target)

    if is_ajax:
        return ajax_response(True, cguid)
    else:
        return redirect(url_for("upload_success"))


def ajax_response(status, msg):
    status_code = "ok" if status else "error"
    return json.dumps(dict(
        status=status_code,
        msg=msg,
    ))