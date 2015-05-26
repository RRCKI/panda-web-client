import commands
import time
import re
from taskbuffer.JobSpec import JobSpec
from taskbuffer.FileSpec import FileSpec
from common.NrckiLogger import NrckiLogger
from ui.Actions import movedata
import userinterface.Client as Client
from db.models import *
from common import client_config
_logger = NrckiLogger().getLogger("JobMaster")

class JobMaster:
    def __init__(self):
        self.jobList = []
        self.fileList = []
        self.dbhost = client_config.DB_HOST
        self.dbname = client_config.DB_DATABASE
        self.dbport = client_config.DB_PORT
        self.dbtimeout = 0
        self.dbuser = client_config.DB_USERNAME
        self.dbpasswd = client_config.DB_PASSWORD
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
        cont = s.query(Container).filter(Container.id == job.container).one()
        input_files = cont.files
        owner = job.owner

        isOK = True
        for f in input_files:
            hasReplica = False
            replicas = f.replicas
            if len(replicas) != 0:
                for r in replicas:
                    if r.se == client_config.DEFAULT_SE:
                        if r.status == 'ready':
                            hasReplica = True
                        elif r.status == 'transferring':
                            pass
                if not hasReplica:
                    #TODO Send message to clone replica
                    pass
            else:
                #TODO Send message to make replica
                pass
            if not hasReplica:
                isOK = False
                # Send message to make replica



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
        pandajob.prodDBlock = "%s:%s.%s" % (scope, scope, job.jobName)

        pandajob.jobParameters = '%s %s "%s"' % (release, distributive, parameters)

        for file in input_files:
            fileIT = FileSpec()
            fileIT.lfn = file
            fileIT.dataset = pandajob.prodDBlock
            fileIT.prodDBlock = pandajob.prodDBlock
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



