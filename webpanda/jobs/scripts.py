from datetime import datetime
import time

from taskbuffer.JobSpec import JobSpec
from taskbuffer.FileSpec import FileSpec
import userinterface.Client as Client
from flask import current_app

from webpanda.common import client_config
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.ddm.DDM import SEFactory
from webpanda.ddm.scripts import ddm_localextractfile
from webpanda.files import Replica, File
from webpanda.files.common import getScope, getFullPath, getGUID
from webpanda.jobs import Job
from webpanda.services import sites_, jobs_, replicas_, files_
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

    jobList = []

    site = sites_.get(siteid)

    job = jobs_.get(int(jobid))
    cont = job.container
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
            replica = Replica()
            replica.se = site.se
            replica.status = 'defined'
            replica.lfn = getFullPath(f.scope, pandajob.jobName, f.lfn)
            replica.original = f
            replicas_.save(replica)

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

    # Register file in container
    fc.reg_file_in_cont(log, cont, 'log')

    replica = Replica()
    replica.se = pandajob.destinationSE
    replica.status = 'defined'
    replica.lfn = getFullPath(log.scope, pandajob.jobName, log.lfn)
    replica.original = log
    replicas_.save(replica)

    jobList.append(pandajob)

    #submitJob
    o = submitJobs(jobList)
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
    for job in jobs:
        ids.append(job.id)
        site = sites_.first(ce=job.ce)
        cont = job.container
        cc = cont.files

        update_info = False

        slist = {}
        if job.status == 'finished':
            slist['output'] = 'ready'
            slist['log'] = 'ready'
            update_info = True
        elif job.status == 'failed':
            slist['output'] = 'failed'
            slist['log'] = 'ready'
        elif job.status == 'cancelled':
            slist['output'] = 'failed'
            slist['log'] = 'ready'
        else:
            continue

        for c in cc:
            if c.type in ['output', 'log']:
                f = c.file
                for replica in f.replicas:
                    if replica.se == site.se:
                        # Update replica status
                        replica.status = slist[c.type]
                        replicas_.save(replica)

                        if update_info:
                            conn_factory = SEFactory()
                            connector = conn_factory.getSE(site.plugin, None)
                            f.fsize = connector.fsize(replica.lfn)
                            f.md5sum = connector.md5sum(replica.lfn)
                            f.checksum = connector.adler32(replica.lfn)
                            f.modification_time = datetime.utcnow()
                            fc.save(f)

        job.registered = 1
        job.registation_time = datetime.utcnow()
        jobs_.save(job)

    return ids
