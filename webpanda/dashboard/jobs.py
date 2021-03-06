# -*- coding: utf-8 -*-
from base64 import b64decode
from datetime import datetime

from celery import chord
from flask import Blueprint, jsonify, request, render_template, url_for, make_response, g, current_app, session
from werkzeug.utils import redirect

from webpanda.jobs.scripts import extractLog
from webpanda.async import prepareInputFiles, async_kill_job, async_send_job
from webpanda.common.utils import find
from webpanda.dashboard import route_s
from webpanda.ddm.scripts import ddm_checkexternalifexists, ddm_getlocalabspath
from webpanda.files.models import File, Replica
from webpanda.files.scripts import register_ftp_files, getUrlInfo
from webpanda.files.common import getGUID, getScope
from webpanda.jobs import Job
from webpanda.jobs.forms import NewJobForm, JobResendForm, JobKillForm
from webpanda.services import distrs_, jobs_, conts_, files_, replicas_
from webpanda.services import sites_
from webpanda.fc import client as fc

bp = Blueprint('jobs', __name__, url_prefix="/jobs")


@route_s(bp, "/", methods=['GET'])
def jobs():
    """
    List of user's jobs view
    :return: Response obj
    """
    hours_limit = request.args.get('hours', current_app.config['HOURS_LIMIT'], type=int)
    display_limit = request.args.get('display_limit', current_app.config['DISPLAY_LIMIT'], type=int)
    session['hours_limit'] = hours_limit
    session['display_limit'] = display_limit
    return render_template("dashboard/jobs/list.html")


@route_s(bp, "/list", methods=['GET'])
def jobs_list():
    """
    Get list of jobs method for ajax
    :return: List of Job obj
    """
    user = g.user

    hours_limit = session.get('hours_limit', current_app.config['HOURS_LIMIT'])
    display_limit = session.get('display_limit', current_app.config['DISPLAY_LIMIT'])
    status = request.args.get('status', "")
    tags = request.args.get('tag', "")

    # show users jobs
    jobs = jobs_.find(owner_id=user.id).filter(Job.status.contains(status)).filter(Job.tags.contains(tags)).order_by(Job.id.desc()).limit(display_limit)

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
        job_o['attemptnr'] = job.attemptnr
        jobs_o.append(job_o)
    data = {}
    data['data'] = jobs_o

    return make_response(jsonify(data), 200)


@route_s(bp, "/<id>", methods=['GET'])
def job_info(id):
    """
    Job info view
    :param guid: guid of job
    :return: Response obj
    """
    job = jobs_.get(id)
    container = job.container
    resend_form = JobResendForm()
    kill_form = JobKillForm()
    return render_template("dashboard/jobs/job.html", job=job, files=container.files, ftp=current_app.config['FTP'], resend_form=resend_form, kill_form=kill_form)


@route_s(bp, "/new", methods=['GET', 'POST'])
def job():
    """
    New job form view
    :return: Response obj
    """
    form = NewJobForm(request.form)
    if request.method == 'POST':
        site = sites_.get(int(form.site.data))
        distr_name, distr_release = form.distr.data.split(':')
        distr = distrs_.first(name=distr_name, release=int(distr_release))

        container_guid = form.container.data
        try:
            container = conts_.first(guid=container_guid)
        except(Exception):
            _logger.error(Exception.message)
            return make_response(jsonify({'error': 'Container not found'}), 404)

        if site.encode_commands:
            # By default frontend encodes with base64 job script parts separated by ";"
            # It requires script wrapper on cluster side
            jparams = form.params.data
        else:
            # Set site.encode_commands as False if you want to send command string without base64 encoding
            jparams = ';'.join([b64decode(command) for command in form.params.data.split(';')])

        ifiles = request.form.getlist('ifiles[]')
        iguids = request.form.getlist('iguids[]')
        iconts = request.form.getlist('iconts[]')
        ofiles = ['{guid}.out.tgz'.format(guid=container.guid)]

        scope = getScope(g.user.username)

        # Process ftp files
        ftp_dir = form.ftpdir.data
        register_ftp_files(ftp_dir, scope, container.guid)

        # Process guid list
        for f in iguids:
            if f != '':
                file = files_.first(guid=f)
                if file is not None:
                    # Register files in container
                    fc.reg_file_in_cont(file, container, 'input')
                else:
                    return make_response(jsonify({'error': "GUID {} not found".format(f)}))

        # Process containers
        for c in iconts:
            if c != '':
                try:
                    form_cont = conts_.first(guid=c)
                except(Exception):
                    _logger.error(Exception.message)
                    return make_response(jsonify({'error': 'Container in form not found'}), 404)
                for f in form_cont.files:
                    # Register file in catalog
                    fc.reg_file_in_cont(f.file, container, 'input')

        # Processes urls
        for f in ifiles:
            if f != '':
                from_se, path, token = getUrlInfo(f)
                replfn = ':/'.join([from_se, path])

                # Check if used before
                file_id = ddm_checkexternalifexists('', replfn)
                if file_id:
                    file = files_.get(file_id)
                else:
                    lfn = path.split('/')[-1]
                    guid = getGUID(scope, lfn)

                    file = File()
                    file.scope = scope
                    file.guid = guid
                    file.type = 'input'
                    file.lfn = lfn
                    file.status = 'defined'
                    files_.save(file)

                    replica = Replica()
                    replica.se = from_se
                    replica.status = 'link'
                    # Separate url & token
                    replica.lfn = replfn
                    replica.token = token
                    replica.original = file
                    replicas_.save(replica)

                # Register file in container
                fc.reg_file_in_cont(file, container, 'input')

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
            files_.save(file)

            # Register file in container
            fc.reg_file_in_cont(file, container, 'output')

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
        job.params = jparams
        job.distr = distr
        job.container = container
        job.creation_time = datetime.utcnow()
        job.modification_time = datetime.utcnow()
        job.ninputfiles = nifiles
        job.noutputfiles = nofiles
        job.corecount = form.corecount.data
        job.tags = form.tags.data if form.tags.data != "" else None
        jobs_.save(job)

        # Async sendjob
        res = chord(ftasks)(async_send_job.s(jobid=job.id, siteid=site.id))

        return redirect(url_for('jobs.jobs'))

    form.distr.choices = [("%s:%s" % (distr.name, distr.release), "%s: %s" % (distr.name, distr.version)) for distr in distrs_.find().order_by('name').order_by('version')]
    form.site.choices = [(site.id, "{ce}".format(ce=site.ce)) for site in sites_.find(active=1).order_by('ce')]
    return render_template("dashboard/jobs/new.html", form=form)


@route_s(bp, '/<id>/logs', methods=['GET'])
def jobLog(id):
    """
    Returns job stdout & stderr
    :param id: Job id
    :return: json data
    """
    job = jobs_.get(id=id)
    extractLog(id)
    locdir = '/%s/.sys/%s' % (getScope(job.owner.username), job.container.guid)
    absdir = ddm_getlocalabspath(locdir)
    fout = find('payload_stdout.txt', absdir)
    ferr = find('payload_stderr.txt', absdir)
    out = ''
    err = ''
    if len(fout) > 0:
        with open(fout[0]) as f:
            out = f.read()
    if len(ferr) > 0:
        with open(ferr[0]) as f:
            err = f.read()
    data = {}
    data['id'] = id
    data['out'] = out
    data['err'] = err
    return make_response(jsonify({'data': data}), 200)


@route_s(bp, '/resend', methods=['POST'])
def job_resend():
    """
    Initiate job resend
    :return: Response obj
    """
    form = JobResendForm()
    if request.method == 'POST':
        id_ = int(form.id_.data)
        job = jobs_.get(id_)
        pandaid = job.pandaid

        return redirect(url_for('jobs.jobs'))
    return make_response(jsonify({'status': 'Page not found'}), 404)


@route_s(bp, '/kill', methods=['POST'])
def job_kill():
    """
    Initiate job kill
    :return: Response obj
    """
    form = JobKillForm()
    if request.method == 'POST':
        id_ = int(form.id_.data)
        job = jobs_.get(id=id_)
        pandaid = job.pandaid
        if pandaid is not None:
            out = async_kill_job(pandaid)
            return make_response(jsonify({'data': out}), 200)
        return redirect(url_for('jobs.jobs'))
    return make_response(jsonify({'status': 'Page not found'}), 404)

