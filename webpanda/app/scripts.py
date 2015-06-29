# -*- coding: utf-8 -*-
from datetime import datetime
import os
from flask import g
from app import app, db

from common.utils import adler32, fsize
from common.utils import md5sum
from models import Container, Site, File, Replica, Job
from common.NrckiLogger import NrckiLogger
from ui.FileMaster import getScope, getGUID, cloneReplica, setFileMeta
import userinterface.Client as Client

_logger = NrckiLogger().getLogger('app.scripts')

def registerLocalFile(arg, dirname, names):
    """Register files from local dir to container
    :param arg:
    :param dirname:
    :param names:
    :return:
    """
    site = Site.query.filter_by(se=app.config['DEFAULT_SE']).first()
    _logger.debug(str(arg))
    cont = Container.query.filter_by(guid=arg).first()
    files = cont.files

    for name in names:
        fpath = os.path.join(dirname, name)

        fobj = None
        for file in files:
            if file.lfn == name:
                fobj = file
        if not fobj:
            fobj = File()
            fobj.scope = getScope(g.user.username)
            fobj.lfn = name
            fobj.guid = getGUID(fobj.scope, fobj.lfn)
            fobj.type = 'input'
            fobj.status = 'defined'
            fobj.containers.append(cont)
            db.session.add(fobj)
            db.session.commit()
            setFileMeta(fobj.id, fpath)

        replicas = fobj.replicas
        replica = None
        for r in replicas:
            if r.se == site.se and r.status == 'ready':
                pass
        if not replica:
            replica = Replica()
            replica.se = site.se
            replica.status = 'ready'
            replica.token = ''
            replica.lfn = fpath
            replica.original = fobj
            db.session.add(replica)
            db.session.commit()

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
                        job.status = obj.jobStatus
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