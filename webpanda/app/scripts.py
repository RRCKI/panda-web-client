# -*- coding: utf-8 -*-
from datetime import datetime
import os

from flask import g
import userinterface.Client as Client

from webpanda.app import app, db
from webpanda.common.utils import adler32, fsize
from webpanda.common.utils import md5sum
from webpanda.ddm.DDM import ddm_checkifexists, ddm_localmakedirs, ddm_localcp, ddm_localextractfile
from webpanda.app.models import Container, Site, File, Replica, Job
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.ui.FileMaster import getScope, getGUID, cloneReplica, setFileMeta


_logger = NrckiLogger().getLogger('app.scripts')

def registerLocalFile(arg, dirname, names):
    """Register files from local dir to container
    :param arg: Container guid
    :param dirname: Abs dir
    :param names: File name
    :return:
    """
    site = Site.query.filter_by(se=app.config['DEFAULT_SE']).first()
    _logger.debug(str(arg))
    cont = Container.query.filter_by(guid=arg).first()
    files = cont.files

    for name in names:
        fpath = os.path.join(dirname, name)

        fobj = None
        # Check in container
        for file in files:
            if file.lfn == name:
                fobj = file

        # Check in catalog
        if not fobj:
            destination = os.path.join(dirname, name)
            adler = adler32(destination)
            md5 = md5sum(destination)
            size = fsize(destination)
            file_id = ddm_checkifexists(name, size, adler, md5)

            if file_id:
                # If file exists
                fobj = File.query.filter_by(id=file_id).one()

        if not fobj:
            fobj = File()
            fobj.scope = getScope(g.user.username)
            fobj.lfn = name
            fobj.guid = getGUID(fobj.scope, fobj.lfn)
            fobj.type = 'input'
            fobj.status = 'defined'
            db.session.add(fobj)
            db.session.commit()
            setFileMeta(fobj.id, fpath)

        cont.files.append(fobj)
        db.session.add(cont)
        db.session.commit()

        replicas = fobj.replicas
        replica = None
        for r in replicas:
            if r.se == site.se and r.status == 'ready':
                replica = r
        if not replica:
            ldir = '/' + os.path.join('system', fobj.scope, fobj.guid)
            ddm_localmakedirs(ldir)
            ddm_localcp(fpath[len(site.datadir):], ldir)

            replica = Replica()
            replica.se = site.se
            replica.status = 'ready'
            replica.token = ''
            replica.lfn = os.path.join(ldir, fobj.lfn)
            replica.original = fobj
            db.session.add(replica)
            db.session.commit()

def register_ftp_files(ftp_dir, guid):
    if ftp_dir == '':
        return []

    dir_name = os.path.join(app.config['UPLOAD_FOLDER'], getScope(g.user.username), ftp_dir)
    ftp_walk = os.walk(dir_name)
    for item in ftp_walk:
        # Calculate files' hash, size
        # Register it If db hasn't similar file
        registerLocalFile(guid, item[0], item[2])

def updateJobStatus():
    # Method to sync PandaDB job status and local job status
    # show users jobs
    jobs = Job.query.filter(Job.pandaid.isnot(None))\
        .filter(~Job.status.in_(['finished', 'failed', 'cancelled']))\
        .all()

    ids = []
    localids = []
    for job in jobs:
        localids.append(job.id)
        ids.append(job.pandaid)

    # get status update
    if len(ids) > 0:
        _logger.debug('getJobStatus: ' + str(ids))
        s, o = Client.getJobStatus(ids)
        for job in jobs:
            if job.pandaid in ids:
                for obj in o:
                    if obj.PandaID == job.pandaid:
                        if job.status != obj.jobStatus:
                            job.status = obj.jobStatus
                            job.modification_time = datetime.utcnow()
                            db.session.add(job)
                            db.session.commit()

    return localids

def registerOutputFiles():
    jobs = Job.query.filter(Job.status.in_(['finished', 'failed', 'cancelled']))\
        .filter(Job.registered != 1)\
        .all()
    ids = []
    for job in jobs:
        ids.append(job.id)
        site = Site.query.filter_by(ce=job.ce).first()
        cont = job.container
        files = cont.files

        slist = {}
        if job.status == 'finished':
            slist['output'] = 'ready'
            slist['log'] = 'ready'
        elif job.status == 'failed':
            slist['output'] = 'failed'
            slist['log'] = 'ready'
        elif job.status == 'cancelled':
            slist['output'] = 'failed'
            slist['log'] = 'ready'
        else:
            continue

        for file in files:
            if file.type in ['output', 'log']:
                replicas = file.replicas
                for replica in replicas:
                    if replica.se == site.se:
                        # Update replica status
                        replica.status = slist[file.type]
                        db.session.add(replica)
                        db.session.commit()

        job.registered = 1
        job.registation_time = datetime.utcnow()
        db.session.add(job)
        db.session.commit()

    return ids

def transferOutputFiles(ids=[]):
    if len(ids) == 0:
        return 0
    to_site = Site.query.filter_by(se=app.config['DEFAULT_SE']).first()
    jobs = Job.query.filter(Job.id.in_(ids)).all()
    for job in jobs:
        from_site = Site.query.filter_by(ce=job.ce).first()
        cont = job.container
        files = cont.files
        for file in files:
            if file.type in ['log', 'output']:
                replicas = file.replicas
                needReplica = False
                fromReplica = 0
                hasReplica = False
                for replica in replicas:
                    if replica.se == from_site.se and replica.status == 'ready':
                       needReplica = True
                       fromReplica = replica.id
                    if replica.se == to_site.se:
                        if replica.status == 'ready':
                            hasReplica = True
                            setFileMeta(file.id, app.config['DATA_PATH'] + replica.lfn)
                        if replica.status != 'ready':
                            raise Exception('Broken replica. File: %s' % file.guid)
                if needReplica and not hasReplica:
                    task = cloneReplica.delay(fromReplica, to_site.se)

    return 0

def extractLog(id):
    """
    Finds local log archive and extracts it
    :param id: Job id
    :return:
    """
    job = Job.query.filter_by(id=id).first()
    files = job.container.files
    for f in files:
        if f.type == 'log':
            replicas = f.replicas
            for r in replicas:
                if r.se == app.config['DEFAULT_SE'] and r.status == 'ready' and r.lfn.endswith('.log.tgz'):
                    ddm_localextractfile(r.lfn)

def extractOutputs(id):
    """
    Finds local output archives and extracts it
    :param id: Job id
    :return:
    """
    job = Job.query.filter_by(id=id).first()
    files = job.container.files
    for f in files:
        if f.type == 'output':
            replicas = f.replicas
            for r in replicas:
                if r.se == app.config['DEFAULT_SE'] and r.status == 'ready' and r.lfn.endswith('.tgz'):
                    ddm_localextractfile(r.lfn)