# -*- coding: utf-8 -*-
import commands
from datetime import datetime
from celery import chord
from flask import Blueprint, request, g, current_app

from webpanda.api import route_s
from webpanda.app.scripts import extractLog
from webpanda.async import prepareInputFiles, async_send_job
from webpanda.common.utils import find
from webpanda.core import WebpandaError
from webpanda.ddm.scripts import ddm_getlocalabspath
from webpanda.files import Container, File
from webpanda.files.scripts import getScope, getGUID, register_ftp_files
from webpanda.jobs import Job
from webpanda.services import jobs_, distrs_, conts_, sites_, files_
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.fc.Client import Client as fc


bp = Blueprint('main', __name__)
_logger = NrckiLogger().getLogger("api.main")


@route_s(bp, '/sw', methods=['GET'])
def sw_list():
    """Returns list of available software"""
    g.user = request.oauth.user

    ds = distrs_.all()
    dlist = list()
    for d in ds:
        a = {}
        a['id'] = d.id
        a['name'] = d.name
        a['version'] = d.version
        dlist.append(a)
    return dlist


@route_s(bp, '/container/<guid>/list', methods=['GET'])
def container_list(guid):
    """Returns list of files registered in container"""
    g.user = request.oauth.user

    cont = conts_.first(guid=guid)
    files = cont.files

    datalist = []
    for file in files:
        data = {}
        data['lfn'] = file.lfn
        data['guid'] = file.guid
        data['modification_time'] = str(file.modification_time)
        data['fsize'] = file.fsize
        data['adler32'] = file.checksum
        data['md5sum'] = file.md5sum
        data['scope'] = file.scope
        datalist.append(data)
    return datalist


@route_s(bp, '/job', methods=['POST'])
def new_job():
    """Creates new job
    """
    g.user = request.oauth.user
    scope = getScope(request.oauth.user.username)

    js = request.json
    data = js['data']

    distr_id = data['sw_id']
    params = data['script']
    corecount = data['cores']

    site = sites_.first(ce=current_app.config['DEFAULT_CE'])
    distr = distrs_.get(id)

    container = Container()
    guid = 'job.' + commands.getoutput('uuidgen')
    container.guid = guid
    container.status = 'open'
    conts_.save(container)

    # Process ftp files
    if 'ftp_dir' in data.keys():
        ftp_dir = data['ftp_dir']
        register_ftp_files(ftp_dir, scope, container.guid)

    # Process guid list
    if 'guids' in data.keys():
        guids = data['guids']
        for f in guids:
            if f != '':
                file_ = files_.first(guid=f)
                if file_ is not None:
                    # Register file in catalog
                    fc.reg_file_in_cont(file_, container, 'input')
                else:
                    raise WebpandaError('File with guid %s not found' % f)

    ofiles = ['results.tgz']

    # Starts cloneReplica tasks
    ftasks = prepareInputFiles(container.id, site.se)

    # Saves output files meta
    for lfn in ofiles:
        file = File()
        file.scope = scope
        file.guid = getGUID(scope, lfn)
        file.lfn = lfn
        file.status = 'defined'
        files_.save(file)

        # Register file in catalog
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
    job.owner = request.oauth.user
    job.params = params
    job.distr = distr
    job.container = container
    job.creation_time = datetime.utcnow()
    job.modification_time = datetime.utcnow()
    job.ninputfiles = nifiles
    job.noutputfiles = nofiles
    job.corecount = corecount
    job.tags = data['tags'] if 'tags' in data.keys() else ""
    jobs_.save(job)

    # Async sendjob
    res = chord(ftasks)(async_send_job.s(jobid=job.id, siteid=site.id))
    return {'id': job.id, 'container_id': guid}


@route_s(bp, '/job/<id>/info', methods=['GET'])
def jobStatusAPI(id):
    """Returns job status"""
    g.user = request.oauth.user

    job = jobs_.get_or_404(id)
    data = dict()
    data['id'] = job.id
    data['panda_id'] = job.pandaid
    data['creation_time'] = str(job.creation_time)
    data['modification_time'] = str(job.modification_time)
    data['status'] = job.status
    return data


@route_s(bp, '/job/<id>/logs', methods=['GET'])
def jobLogAPI(id):
    """Returns job stdout & stderr"""
    g.user = request.oauth.user

    job = jobs_.get(id)
    extractLog(id)
    locdir = '/%s/.sys/%s' % (getScope(job.owner.username), job.container.guid)
    absdir = ddm_getlocalabspath(locdir)
    fout = find('payload.stdout', absdir)
    ferr = find('payload.stderr', absdir)
    out = ''
    err = ''
    if len(fout) > 0:
        with open(fout[0]) as f:
            out = f.read()
    if len(ferr) > 0:
        with open(ferr[0]) as f:
            err = f.read()
    data = dict()
    data['id'] = id
    data['out'] = out
    data['err'] = err
    return data
