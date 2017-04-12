from datetime import datetime
import time

from taskbuffer.JobSpec import JobSpec
from taskbuffer.FileSpec import FileSpec
import userinterface.Client as Client
from flask import current_app
import os

from webpanda.common import client_config
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.ddm.DDM import SEFactory
from webpanda.ddm.scripts import ddm_localextractfile
from webpanda.files import File
from webpanda.files.common import getScope, getGUID
from webpanda.jobs import Job
from webpanda.services import sites_, jobs_, replicas_, files_, users_
from webpanda.fc import client as fc

_logger = NrckiLogger().getLogger("files.scripts")


def submitJobs(jobList):
    print 'Submit jobs'
    _logger.debug('Submit jobs')
    _logger.debug(str(jobList))
    s,o = Client.submitJobs(jobList)
    _logger.debug("---------------------")
    _logger.debug(s)

    for x in o:
        _logger.debug("PandaID=%s" % x[0])
    return o


def killJobs(jobList):
    print 'Kill jobs'
    _logger.debug('Kill jobs')
    _logger.debug(str(jobList))
    s,o = Client.killJobs(jobList) # Code 3 eqs. aborted status
    _logger.debug("---------------------")
    _logger.debug(s)
    _logger.debug(o)
    return o


def send_job(jobid, siteid):
    _logger.debug('Jobid: ' + str(jobid))

    site = sites_.get(siteid)

    job = jobs_.get(int(jobid))
    user = users_.get(job.owner_id)
    cont = job.container
    cont_path = fc.get_cont_dir(cont, fc.get_scope(user))
    files_catalog = cont.files

    fscope = getScope(job.owner.username)
    datasetName = '{}:{}'.format(fscope, cont.guid)

    distributive = job.distr.name
    release = job.distr.release
    parameters = job.params

    pandajob = JobSpec()
    pandajob.jobDefinitionID = int(time.time()) % 10000
    pandajob.jobName = cont.guid
    pandajob.transformation = client_config.DEFAULT_TRF
    pandajob.destinationDBlock = datasetName
    pandajob.destinationSE = site.se
    pandajob.currentPriority = 1000
    pandajob.prodSourceLabel = 'user'
    pandajob.computingSite = site.ce
    pandajob.cloud = 'RU'
    pandajob.VO = 'atlas'
    pandajob.prodDBlock = "%s:%s" % (fscope, pandajob.jobName)
    pandajob.coreCount = job.corecount

    pandajob.jobParameters = '%s %s %s "%s"' % (cont.guid, release, distributive, parameters)

    rlinkdir = '/' + '/'.join(pandajob.prodDBlock.split(':'))

    for fcc in files_catalog:
        if fcc.type == 'input':
            f = fcc.file
            guid = f.guid
            fileIT = FileSpec()
            fileIT.lfn = f.lfn
            fileIT.dataset = pandajob.prodDBlock
            fileIT.prodDBlock = pandajob.prodDBlock
            fileIT.type = 'input'
            fileIT.scope = fscope
            fileIT.status = 'ready'
            fileIT.GUID = guid
            pandajob.addFile(fileIT)
            #linkFile(file.id, site.se, rlinkdir)
        if fcc.type == 'output':
            f = fcc.file
            fileOT = FileSpec()
            fileOT.lfn = f.lfn
            fileOT.destinationDBlock = pandajob.prodDBlock
            fileOT.destinationSE = pandajob.destinationSE
            fileOT.dataset = pandajob.prodDBlock
            fileOT.type = 'output'
            fileOT.scope = fscope
            fileOT.GUID = f.guid
            pandajob.addFile(fileOT)

            # Save replica meta
            fc.new_replica(f, site)

    # Prepare lof file
    fileOL = FileSpec()
    fileOL.lfn = "%s.log.tgz" % pandajob.jobName
    fileOL.destinationDBlock = pandajob.destinationDBlock
    fileOL.destinationSE = pandajob.destinationSE
    fileOL.dataset = '{}:logs'.format(fscope)
    fileOL.type = 'log'
    fileOL.scope = 'panda'
    pandajob.addFile(fileOL)

    # Save log meta
    log = File()
    log.scope = fscope
    log.lfn = fileOL.lfn
    log.guid = getGUID(log.scope, log.lfn)
    log.type = 'log'
    log.status = 'defined'
    files_.save(log)

    # Save replica meta
    fc.new_replica(log, site)

    # Register file in container
    fc.reg_file_in_cont(log, cont, 'log')

    # Submit job
    o = submitJobs([pandajob])
    x = o[0]

    try:
        #update PandaID
        PandaID = int(x[0])
        job.pandaid = PandaID
        job.ce = site.ce
    except:
        job.status = 'submit_error'
    jobs_.save(job)

    return 0


def extractLog(id):
    """
    Finds local log archive and extracts it
    :param id: Job id
    :return:
    """
    job = jobs_.get(id)
    files = job.container.files
    for f in files:
        if f.type == 'log':
            replicas = f.replicas
            for r in replicas:
                if r.se == current_app.config['DEFAULT_SE'] and r.status == 'ready' and r.lfn.endswith('.log.tgz'):
                    ddm_localextractfile(r.lfn)


def extractOutputs(id):
    """
    Finds local output archives and extracts it
    :param id: Job id
    :return:
    """
    job = jobs_.get(id)
    files = job.container.files
    for f in files:
        if f.type == 'output':
            replicas = f.replicas
            for r in replicas:
                if r.se == current_app.config['DEFAULT_SE'] and r.status == 'ready' and r.lfn.endswith('.tgz'):
                    ddm_localextractfile(r.lfn)


def update_status():
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
        _logger.debug(o)
        for job in jobs:
            if job.pandaid in ids:
                for obj in o:
                    if obj.PandaID == job.pandaid:
                        # Update attemptNr if changed
                        if job.attemptnr not in [obj.attemptNr]:
                            job.attemptnr = obj.attemptNr
                            jobs_.save(job)

                        # Update status if changed
                        if job.status != obj.jobStatus:
                            job.status = obj.jobStatus
                            job.modification_time = datetime.utcnow()
                            jobs_.save(job)

    return localids


def register_outputs():
    jobs = jobs_.find().filter(Job.status.in_(['finished', 'failed', 'cancelled']))\
        .filter(Job.registered != 1)\
        .all()

    ids = []
    conn_factory = SEFactory()

    for job in jobs:
        ids.append(job.id)
        user = users_.get(job.owner_id)
        site = sites_.first(ce=job.ce)
        cont = job.container
        cont_path = fc.get_cont_dir(cont, fc.get_scope(user))
        cc = cont.files

        out_ready = False
        if job.status == 'finished':
            out_ready = True

        for c in cc:
            if c.type not in ["log", "output"]:
                continue

            f = c.file
            for replica in f.replicas:
                if replica.se == site.se:
                    if c.type == 'output' and not out_ready:
                        # Update replica status
                        replica.status = "failed"
                        replicas_.save(replica)
                    else:
                        connector = conn_factory.getSE(site.plugin, None)

                        # link real file to saved replica
                        fpath = os.path.join(cont_path, f.lfn)
                        # append attemptnr
                        if job.attemptnr > 0:
                            fpath += "." + str(job.attemptnr)

                        #connector.link(os.path.join(cont_path, f.lfn), replica_dir, rel=True)
                        connector.mv(fpath, replica.lfn, rel=True)

                        # get replica info
                        f.fsize = connector.fsize(replica.lfn)
                        f.md5sum = connector.md5sum(replica.lfn)
                        f.checksum = connector.adler32(replica.lfn)
                        f.modification_time = datetime.utcnow()
                        fc.save(f)

                        # Update replica status
                        replica.status = "ready"
                        replicas_.save(replica)

        job.registered = 1
        job.registation_time = datetime.utcnow()
        jobs_.save(job)

    return ids
