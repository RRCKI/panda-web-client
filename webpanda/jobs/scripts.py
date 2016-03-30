import time

from taskbuffer.JobSpec import JobSpec
from taskbuffer.FileSpec import FileSpec
import userinterface.Client as Client

from webpanda.common import client_config
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.db.models import DB, Site, Job, Replica, File
from webpanda.files.scripts import getScope, getFullPath, getGUID

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

    # Initialize db
    s = DB().getSession()

    site = s.query(Site).filter(Site.id == siteid).one()

    job = s.query(Job).filter(Job.id == int(jobid)).one()
    cont = job.container
    files = cont.files

    scope = client_config.DEFAULT_SCOPE
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

    for file in files:
        if file.type == 'input':
            guid = file.guid
            fileIT = FileSpec()
            fileIT.lfn = file.lfn
            fileIT.dataset = pandajob.prodDBlock
            fileIT.prodDBlock = pandajob.prodDBlock
            fileIT.type = 'input'
            fileIT.scope = fscope
            fileIT.status = 'ready'
            fileIT.GUID = guid
            pandajob.addFile(fileIT)
            #linkFile(file.id, site.se, rlinkdir)
        if file.type == 'output':
            fileOT = FileSpec()
            fileOT.lfn = file.lfn
            fileOT.destinationDBlock = pandajob.prodDBlock
            fileOT.destinationSE = pandajob.destinationSE
            fileOT.dataset = pandajob.prodDBlock
            fileOT.type = 'output'
            fileOT.scope = fscope
            fileOT.GUID = file.guid
            pandajob.addFile(fileOT)

            # Save replica meta
            replica = Replica()
            replica.se = site.se
            replica.status = 'defined'
            replica.lfn = getFullPath(file.scope, pandajob.jobName, file.lfn)
            replica.original = file
            s.add(replica)
            s.commit()

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
    log.containers.append(cont)
    s.add(log)
    s.commit()

    replica = Replica()
    replica.se = pandajob.destinationSE
    replica.status = 'defined'
    replica.lfn = getFullPath(log.scope, pandajob.jobName, log.lfn)
    replica.original = log
    s.add(replica)
    s.commit()

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
    s.add(job)
    s.commit()
    s.close()

    return 0