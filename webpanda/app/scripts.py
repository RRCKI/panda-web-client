# -*- coding: utf-8 -*-
from datetime import datetime
import os
from flask import g
from app import app, db
from common.utils import adler32, fsize
from common.utils import md5sum
from models import Container, Site, File, Replica, Job
from common.NrckiLogger import NrckiLogger
from ui.FileMaster import getScope, getGUID
import userinterface.Client as Client

_logger = NrckiLogger().getLogger('app.scripts')

def registerLocalFile(arg, dirname, names):
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
            fobj.checksum = adler32(fpath)
            fobj.md5sum = md5sum(fpath)
            fobj.fsize = fsize(fpath)
            fobj.modification_time = datetime.utcnow()
            fobj.containers.append(cont)
            db.session.add(fobj)
            db.session.commit()

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
    for job in jobs:
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