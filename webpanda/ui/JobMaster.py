import commands
import json
import time
from mq.MQ import MQ
from taskbuffer.JobSpec import JobSpec
from taskbuffer.FileSpec import FileSpec
from common.NrckiLogger import NrckiLogger
import userinterface.Client as Client
from db.models import *
from common import client_config
from ui.FileMaster import cloneReplica, makeReplica

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

    def run(self, data):
        # Initialize db
        s = DB().getSession()

        jobid = data['id']
        _logger.debug('Jobid: ' + str(jobid))

        job = s.query(Job).filter(Job.id == jobid).one()
        cont = job.container
        input_files = cont.files

        ready_replicas = {}
        for file in input_files:
            replicas = file.replicas
            if replicas.count() != 0:
                for r in replicas:
                    if r.se == client_config.DEFAULT_SE:
                        if r.status == 'ready':
                            ready_replicas[file.guid] = r
                        elif r.status == 'transferring':
                            pass
                if not ready_replicas[file.guid]:
                    # Clone replica from existing
                    cloneReplica(replicas[0].id, client_config.DEFAULT_SE)
            else:
                # Make replica of registered file
                makeReplica(file.id, client_config.DEFAULT_SE)

        datasetName = 'panda:panda.destDB.%s' % commands.getoutput('uuidgen')
        destName    = client_config.DEFAULT_SE
        site = client_config.DEFAULT_SE
        scope = client_config.DEFAULT_SCOPE

        distributive = job.distr.name
        release = job.distr.release
        parameters = job.params
        output_files = ['results.tgz']

        pandajob = JobSpec()
        pandajob.jobDefinitionID = int(time.time()) % 10000
        pandajob.jobName = cont.guid
        pandajob.transformation = client_config.DEFAULT_TRF
        pandajob.destinationDBlock = datasetName
        pandajob.destinationSE = destName
        pandajob.currentPriority = 1000
        pandajob.prodSourceLabel = 'user'
        pandajob.computingSite = site
        pandajob.cloud = 'RU'
        pandajob.prodDBlock = "%s:%s.%s" % (scope, scope, pandajob.jobName)

        pandajob.jobParameters = '%s %s "%s"' % (release, distributive, parameters)

        for file in input_files:
            dataset = "%s:%s" % (scope, file.guid)
            fileIT = FileSpec()
            fileIT.lfn = file
            fileIT.dataset = dataset
            fileIT.prodDBlock = dataset
            fileIT.type = 'input'
            fileIT.scope = scope
            fileIT.status = 'ready'
            fileIT.GUID = commands.getoutput('uuidgen')
            pandajob.addFile(fileIT)

        for file in output_files:
            fileOT = FileSpec()
            fileOT.lfn = file
            fileOT.destinationDBlock = pandajob.prodDBlock
            fileOT.destinationSE = pandajob.destinationSE
            fileOT.dataset = pandajob.prodDBlock
            fileOT.type = 'output'
            fileOT.scope = scope
            fileOT.GUID = commands.getoutput('uuidgen')
            pandajob.addFile(fileOT)


        fileOL = FileSpec()
        fileOL.lfn = "%s.log.tgz" % pandajob.jobName
        fileOL.destinationDBlock = pandajob.destinationDBlock
        fileOL.destinationSE = pandajob.destinationSE
        fileOL.dataset = pandajob.destinationDBlock
        fileOL.type = 'log'
        fileOL.scope = 'panda'
        pandajob.addFile(fileOL)

        self.jobList.append(pandajob)

        #submitJob
        o = self.submitJobs(self.jobList)
        x = o[0]

        #update PandaID
        PandaID = int(x[0])
        job.pandaid = PandaID
        s.add(job)
        s.commit()
        s.close()

        return 0


def mqSendJob(jobid):
    routing_key = client_config.MQ_JOBKEY + '.now'
    mq = MQ(host=client_config.MQ_HOST, exchange=client_config.MQ_EXCHANGE)
    # Create MQ request
    data = {}
    data['id'] = jobid
    message = json.dumps(data)
    print '%s: %s' % ('mqSendJob', jobid)
    mq.sendMessage(message, routing_key)

def mqSendJobDelayed(jobid):
    routing_key = client_config.MQ_JOBKEY + '.delayed'
    mq = MQ(host=client_config.MQ_HOST, exchange=client_config.MQ_EXCHANGE)
    # Create MQ request
    data = {}
    data['id'] = jobid
    message = json.dumps(data)
    print '%s: %s' % ('mqSendJobDelayed', jobid)
    mq.sendMessage(message, routing_key)


