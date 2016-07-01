import time

from pandaserver.taskbuffer.JobSpec import JobSpec
from pandaserver.taskbuffer.FileSpec import FileSpec
import pandaserver.userinterface.Client as Client

from webpanda.common import client_config
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.files import Catalog, Replica, File
from webpanda.files.scripts import getScope, getFullPath, getGUID
from webpanda.services import sites_, jobs_, replicas_, files_, catalog_

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

    for fc in files_catalog:
        if fc.type == 'input':
            f = fc.file
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
        if fc.type == 'output':
            f = fc.file
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

    c = Catalog()
    c.cont = cont
    c.file = log
    c.type = 'log'
    catalog_.save(c)

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
