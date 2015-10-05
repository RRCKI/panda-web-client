import simplejson as json
import time

from taskbuffer.JobSpec import JobSpec
from taskbuffer.FileSpec import FileSpec
import userinterface.Client as Client

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.db.models import *
from webpanda.common import client_config
from webpanda.ui.FileMaster import cloneReplica, getFullPath, getGUID, linkFile, getScope
from webpanda.app import celery

_logger = NrckiLogger().getLogger("JobMaster")

class JobMaster:
    def __init__(self):
        self.jobList = []
        self.fileList = []
        self.table_jobs = 'jobs'

    def submitJobs(self, jobList):
        print 'Submit jobs'
        _logger.debug('Submit jobs')

        s,o = Client.submitJobs(jobList)
        _logger.debug("---------------------")
        _logger.debug(s)

        for x in o:
            _logger.debug("PandaID=%s" % x[0])
        return o

    def send_job(self, jobid, siteid):
        _logger.debug('Jobid: ' + str(jobid))

        # Initialize db
        s = DB().getSession()

        site = s.query(Site).filter(Site.id == siteid).one()

        job = s.query(Job).filter(Job.id == int(jobid)).one()
        cont = job.container
        files = cont.files

        datasetName = 'panda:%s' % cont.guid
        scope = client_config.DEFAULT_SCOPE
        fscope = getScope(job.owner.username)

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
        pandajob.prodDBlock = "%s:%s" % (scope, pandajob.jobName)
        pandajob.coreCount = job.corecount

        pandajob.jobParameters = '%s %s "%s"' % (release, distributive, parameters)

        rlinkdir = '/' + '/'.join(pandajob.prodDBlock.split(':'))

        for file in files:
            if file.type == 'input':
                guid = file.guid
                fileIT = FileSpec()
                fileIT.lfn = file.lfn
                fileIT.dataset = pandajob.prodDBlock
                fileIT.prodDBlock = pandajob.prodDBlock
                fileIT.type = 'input'
                fileIT.scope = scope
                fileIT.status = 'ready'
                fileIT.GUID = guid
                pandajob.addFile(fileIT)
                linkFile(file.id, site.se, rlinkdir)
            if file.type == 'output':
                fileOT = FileSpec()
                fileOT.lfn = file.lfn
                fileOT.destinationDBlock = pandajob.prodDBlock
                fileOT.destinationSE = pandajob.destinationSE
                fileOT.dataset = pandajob.prodDBlock
                fileOT.type = 'output'
                fileOT.scope = scope
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

        fileOL = FileSpec()
        fileOL.lfn = "%s.log.tgz" % pandajob.jobName
        fileOL.destinationDBlock = pandajob.destinationDBlock
        fileOL.destinationSE = pandajob.destinationSE
        fileOL.dataset = 'panda:logs'
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

        self.jobList.append(pandajob)

        #submitJob
        o = self.submitJobs(self.jobList)
        x = o[0]

        #update PandaID
        PandaID = int(x[0])
        job.pandaid = PandaID
        job.ce = site.ce
        s.add(job)
        s.commit()
        s.close()

        return 0

@celery.task(serializer='json')
def send_job(*args, **kwargs):
    jobid = kwargs.get('jobid', 0L)
    siteid = kwargs.get('siteid', 0L)
    if int(jobid) == 0:
        raise Exception('Illegal argument: jobid')
    if int(siteid) == 0:
        raise Exception('Illegal argument: siteid')
    jm = JobMaster()

    return json.dumps(jm.send_job(jobid, siteid))

def prepareInputFiles(cont_id, se):
    # Initialize db
    s = DB().getSession()
    container = s.query(Container).filter(Container.id == cont_id).one()
    files = container.files
    tasks = []
    for file in files:
        replicas_len = file.replicas.count()
        if not replicas_len:
            raise Exception("No available replicas for file %s" % file.guid)
            return
        replicas = file.replicas
        hasReplica = False
        for replica in replicas:
            if replica.se == se and replica.status == 'ready':
                hasReplica = True

        if hasReplica:
            continue
        tasks.append(cloneReplica.s(replicas[0].id, se))
    s.close()
    return tasks
