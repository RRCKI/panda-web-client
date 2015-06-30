# -*- coding: utf-8 -*-
import commands
import glob
import json
from celery import chord
from datetime import datetime

from flask import render_template, flash, redirect, session, url_for, request, g, jsonify, make_response, Response
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db
from app.apis import makeReplicaAPI
from scripts import registerLocalFile
from common.NrckiLogger import NrckiLogger
from common.utils import adler32, fsize, md5sum
from forms import LoginForm, RegisterForm, NewJobForm, NewFileForm
from models import *
from datetime import datetime
import os
from ui.FileMaster import cloneReplica, getScope, getGUID, getUrlInfo, setFileMeta
from ui.JobMaster import send_job, prepareInputFiles

from userinterface import Client

HOURS_LIMIT = 96
DISPLAY_LIMIT = 6000

_logger = NrckiLogger().getLogger("app.views")


@app.before_request
def before_request():
    g.user = current_user
    g.user.last_seen = datetime.utcnow()
    g.user.save()

@app.route('/')
@login_required
def index():
    user = g.user
    return render_template("index.html",
        title = 'Home',
        user = user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = g.user
    if user.is_authenticated():
        # if user is logged in we get out of here
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))
        # log user in
        login_user(user, remember = form.remember_me.data)
        flash('You are now logged in!')
        return redirect(request.args.get("next") or url_for("index"))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        password_again = form.password_again.data
        user = User.query.filter_by(username=username).first()
        if user is not None:
            flash('Попробуйте другой login.')
            return redirect(url_for('register'))
        if password != password_again:
            flash('Пароли не совпадают.')
            return redirect(url_for('register'))
        user = User()
        user.username = username
        user.password = password
        user.active = 0
        user.role = 0
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


#############################################
#############################################

@app.route("/job", methods=['GET', 'POST'])
@login_required
def job():
    """Handle the definition of a job."""
    form = NewJobForm()
    if request.method == 'POST':
        site = Site.query.filter_by(ce=app.config['DEFAULT_CE']).first()
        distr_name, distr_release = form.distr.data.split(':')
        distr = Distributive.query.filter_by(name=distr_name, release=int(distr_release)).first()

        container_guid = form.container.data
        try:
            container = Container.query.filter_by(guid=container_guid).one()
        except(Exception):
            _logger.error(Exception.message)
            return make_response(jsonify({'error': 'Container not found'}), 404)

        ifiles = request.form.getlist('ifiles[]')
        ofiles = ['results.tgz']

        scope = getScope(g.user.username)

        ftpdir = form.ftpdir.data
        if ftpdir != '':
            dir = os.path.join(app.config['UPLOAD_FOLDER'], getScope(g.user.username), ftpdir)
            os.path.walk(dir, registerLocalFile, container.guid)

        # Processes urls
        for f in ifiles:
            if f != '':
                from_se, path, token = getUrlInfo(f)
                lfn = path.split('/')[-1]
                guid = getGUID(scope, lfn)

                file = File()
                file.scope = scope
                file.guid = guid
                file.type = 'input'
                file.lfn = lfn
                file.status = 'defined'
                db.session.add(file)
                db.session.commit()
                container.files.append(file)
                db.session.add(container)
                db.session.commit()

                replica = Replica()
                replica.se = from_se
                replica.status = 'defined'
                # Separate url & token
                replica.lfn = ':'.join([from_se, path])
                replica.token = token
                replica.original = file
                db.session.add(replica)
                db.session.commit()

        # Starts cloneReplica tasks
        ftasks = prepareInputFiles(container.id, site.se)

        # Saves output files meta
        for lfn in ofiles:
            file = File()
            file.scope = scope
            file.guid = getGUID(scope, lfn)
            file.type = 'output'
            file.lfn = lfn
            file.status = 'defined'
            db.session.add(file)
            db.session.commit()
            container.files.append(file)
            db.session.add(container)
            db.session.commit()

        # Counts files
        allfiles = container.files
        nifiles = 0
        nofiles = 0
        for f in allfiles:
            if f.type == 'input':
                nifiles += 1
            if f.type == 'output':
                nofiles += 1

        # Defines job meta
        job = Job()
        job.pandaid = None
        job.status = 'pending'
        job.owner = g.user
        job.params = form.params.data
        job.distr = distr
        job.container = container
        job.creation_time = datetime.utcnow()
        job.modification_time = datetime.utcnow()
        job.ninputfiles = nifiles
        job.noutputfiles = nofiles
        db.session.add(job)
        db.session.commit()

        # Async sendjob
        res = chord(ftasks)(send_job.s(jobid=job.id, siteid=site.id))

        return redirect(url_for('jobs'))

    form.distr.choices = [("%s:%s" % (distr.name, distr.release), "%s: %s" % (distr.name, distr.version)) for distr in Distributive.query.order_by('name').order_by('version')]
    return render_template("pandaweb/jobs_new.html", form=form)

@app.route("/upload", methods=['POST'])
@login_required
def upload():
    form = request.form

    # Create a unique container quid for this particular batch of uploads.
    cguid = 'job.' + commands.getoutput('uuidgen')

    # Is the upload using Ajax, or a direct POST by the form?
    is_ajax = False
    if form.get("__ajax", None) == "true":
        is_ajax = True

    input_files = []

    container = Container()
    container.guid = cguid
    container.status = 'open'
    db.session.add(container)
    db.session.commit()

    for upload in request.files.getlist("file"):
        # Define file params
        lfn = upload.filename.rsplit("/")[0]
        scope = getScope(g.user.username)
        guid = getGUID(scope, lfn)
        site = Site.query.filter_by(se=app.config['DEFAULT_SE']).first()

        # Target folder for these uploads.
        dir = '/' + os.path.join(scope, guid)
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
            # Save metadata
            input_files.append(destination)
            file = File()
            file.scope = scope
            file.guid = guid
            file.type = 'input'
            file.lfn = lfn
            file.token = ''
            file.status = 'defined'
            file.containers.append(container)
            db.session.add(file)
            db.session.commit()
            setFileMeta(file.id, destination)

            replica = Replica()
            replica.se = site.se
            replica.status = 'ready'
            replica.lfn = replfn
            replica.original = file
            db.session.add(replica)
            db.session.commit()
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

@app.route("/jobs", methods=['GET'])
@login_required
def jobs():
    hours_limit = request.args.get('hours', HOURS_LIMIT, type=int)
    display_limit = request.args.get('display_limit', DISPLAY_LIMIT, type=int)
    session['hours_limit'] = hours_limit
    session['display_limit'] = display_limit
    return render_template("pandaweb/jobs_list.html")

@app.route("/jobs/list", methods=['GET'])
@login_required
def jobs_list():
    user = g.user

    hours_limit = session.get('hours_limit', HOURS_LIMIT)
    display_limit = session.get('display_limit', DISPLAY_LIMIT)

    # show users jobs
    jobs = Job.query.filter_by(owner_id=user.id).order_by(Job.id).limit(display_limit)

    # prepare json
    jobs_o = []
    for job in jobs:
        job_o = {}
        job_o['id'] = job.id
        job_o['owner'] = {'id': job.owner.id,
                            'username': job.owner.username}
        job_o['pandaid'] = job.pandaid
        job_o['distr'] = {'id': job.distr.id,
                          'name': job.distr.name,
                          'version': job.distr.version,
                          'str': str(job.distr)}
        job_o['creation_time'] = str(job.creation_time)
        job_o['modification_time'] = str(job.modification_time)
        job_o['status'] = job.status
        job_o['ifiles'] = '[%s] ready' % job.ninputfiles
        job_o['ofiles'] = '[%s]' % job.noutputfiles
        jobs_o.append(job_o)
    data = {}
    data['data'] = jobs_o

    return make_response(jsonify(data), 200)

@app.route("/file", methods=['GET', 'POST'])
@login_required
def file():
    form = NewFileForm()
    if request.method == 'POST':
        se = form.se.data

        from_se, path, token = getUrlInfo(form.url.data)

        file = File()
        file.scope = getScope(g.user.username)
        file.type = 'input'
        file.lfn = path.split('/')[-1]
        file.guid = getGUID(file.scope, file.lfn)
        file.status = 'defined'
        db.session.add(file)
        db.session.commit()
        cont_guid = form.container.data
        if (cont_guid not in [None, '']): # TODO Check regex
            container = Container.query.filter_by(guid=cont_guid).one()
            container.files.append(file)
            db.session.add(container)
            db.session.commit()

        replica = Replica()
        replica.se = from_se
        replica.status = 'ready'
        replica.token = token
        replica.lfn = form.url.data
        replica.original = file
        db.session.add(replica)
        db.session.commit()

        resp = cloneReplica.delay(replica.id, se)
        return redirect(url_for('file_info', guid=file.guid))

    form.se.choices = [("%s" % site.se, "%s" % site.se) for site in Site.query.filter_by(active=1)]
    return render_template("pandaweb/file_new.html", form=form)

@app.route("/file/<guid>", methods=['GET'])
@login_required
def file_info(guid):
    try:
        file = File.query.filter_by(guid=guid).one()
    except(Exception):
        _logger.error(Exception.message)
        return 'File not found'
    return render_template("pandaweb/file.html", file=file, replicas=file.replicas)

@app.route("/file/<guid>/download", methods=['GET'])
@login_required
def file_download(guid):
    try:
        file = File.query.filter_by(guid=guid).one()
    except(Exception):
        _logger.error(Exception.message)
        return make_response(jsonify({'error': 'File not found'}), 404)
    if file.scope != getScope(g.user.username):
        return make_response(jsonify({'error': 'File is not in your scope'}), 403)

    replicas = file.replicas
    for replica in replicas:
        if replica.se == app.config['DEFAULT_SE'] and replica.status == 'ready':
            fullpath = app.config['DATA_PATH'] + replica.lfn
            f = open(fullpath, 'r')
            rr = Response(f.read(), status=200, content_type='application/octet-stream')
            rr.headers['Content-Disposition'] = 'inline; filename="%s"' % file.lfn
            rr.headers['Content-MD5'] = file.md5sum
            file.downloaded += 1
            db.session.add(file)
            db.session.commit()
            return rr
    return make_response(jsonify({'error': 'No ready replica'}), 404)

@app.route("/job/<id>", methods=['GET'])
@login_required
def job_info(id):
    job = Job.query.filter_by(id=id).one()
    container = job.container
    return render_template("pandaweb/job.html", job=job, files=container.files)

@app.route("/files", methods=['GET'])
@login_required
def files():
    hours_limit = request.args.get('hours', HOURS_LIMIT, type=int)
    display_limit = request.args.get('display_limit', DISPLAY_LIMIT, type=int)
    session['hours_limit'] = hours_limit
    session['display_limit'] = display_limit
    return render_template("pandaweb/file_list.html")

@app.route("/file/list", methods=['GET'])
@login_required
def files_list():
    user = g.user

    hours_limit = session.get('hours_limit', HOURS_LIMIT)
    display_limit = session.get('display_limit', DISPLAY_LIMIT)
    scope = getScope(user.username)
    # show users jobs
    files = File.query.filter_by(scope=scope).order_by(File.id).limit(display_limit)

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
