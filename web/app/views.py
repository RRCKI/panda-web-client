# -*- coding: utf-8 -*-
import glob
import json
from uuid import uuid4

from flask import render_template, flash, redirect, session, url_for, request, g, abort, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, RegisterForm, NewJobForm
from models import User, ROLE_USER, ROLE_ADMIN, Distributive, Job
from datetime import datetime
import os

from userinterface import Client

HOURS_LIMIT = 96
DISPLAY_LIMIT = 6000


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
        job = Job()
        job.pandaid = None
        job.status = 'pending'
        job.owner = g.user
        job.distr_id = form.distr.data
        job.params = form.params.data
        job.ifiles = form.ftoken.data
        job.ofiles = form.output_files.data
        job.creation_time = datetime.utcnow()
        job.modification_time = datetime.utcnow()
        db.session.add(job)
        db.session.commit()

        return redirect(url_for('jobs'))

    form.distr.choices = [(distr.id, "%s: %s" % (distr.name, distr.version)) for distr in Distributive.query.order_by('name').order_by('version')]
    return render_template("pandaweb/jobs_new.html", form=form)

@app.route("/upload", methods=['POST'])
@login_required
def upload():
    form = request.form

    # Create a unique "session ID" for this particular batch of uploads.
    upload_key = str(uuid4())

    # Is the upload using Ajax, or a direct POST by the form?
    is_ajax = False
    if form.get("__ajax", None) == "true":
        is_ajax = True

    # Target folder for these uploads.
    target = os.path.join(app.config['UPLOAD_FOLDER'], upload_key)
    try:
        os.mkdir(target)
    except:
        if is_ajax:
            return ajax_response(False, "Couldn't create upload directory: %s" % target)
        else:
            return "Couldn't create upload directory: %s" % target

    input_files = []

    for upload in request.files.getlist("file"):
        filename = upload.filename.rsplit("/")[0]
        destination = os.path.join(target, filename)
        print "Accept incoming file:", filename
        print "Save it to:", destination
        upload.save(destination)
        if os.path.isfile(destination):
            input_files.append(destination)
        else:
            return ajax_response(False, "Couldn't save file: %s" % target)


    if is_ajax:
        return ajax_response(True, upload_key)
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

    ids = []
    for job in jobs:
        if job.pandaid and job.status not in ['finished', 'failed', 'canceled']:
            ids.append(job.pandaid)

    # get status update
    if len(ids) > 0:
        s, o = Client.getJobStatus(ids)
        for job in jobs:
            if job.pandaid in ids:
                for obj in o:
                    if obj.PandaID == job.pandaid:
                        job.status = obj.jobStatus
                        db.session.add(job)
        db.session.commit()

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
                          'version': job.distr.version}
        job_o['creation_time'] = str(job.creation_time)
        job_o['modification_time'] = str(job.modification_time)
        job_o['status'] = job.status
        jobs_o.append(job_o)
    data = {}
    data['data'] = jobs_o

    return json.dumps(data)