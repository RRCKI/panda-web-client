import commands
import time
import re
from taskbuffer.JobSpec import JobSpec
from taskbuffer.FileSpec import FileSpec
from ..common.NrckiLogger import NrckiLogger
from ..ui.Actions import movedata
import userinterface.Client as Client
import MySQLdb
from nrckiclient import config
_logger = NrckiLogger().getLogger("JobMaster")

class JobMaster:
    def __init__(self):
        self.jobList = []
        self.fileList = []
        self.dbhost = config['DB_HOST']
        self.dbname = config['DB_DATABASE']
        self.dbport = config['DB_PORT']
        self.dbtimeout = 0
        self.dbuser = config['DB_USERNAME']
        self.dbpasswd = config['DB_PASSWORD']
        self.table_jobs = 'launcher_job'


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
        datasetName = 'panda:panda.destDB.%s' % commands.getoutput('uuidgen')
        destName    = 'ANALY_RRC-KI-HPC'
        site = 'ANALY_RRC-KI-HPC'
        scope = config['DEFAULT_SCOPE']

        distributive = data['distributive']
        release = data['release']
        parameters = data['parameters']
        input_type = data['input_type']
        input_params = data['input_params']
        input_files = data['input_files']
        output_type = data['output_type']
        output_params = data['output_params']
        output_files = data['output_files']

        jobid = data['jobid']
        _logger.debug('Jobid: ' + str(jobid))

        job = JobSpec()
        job.jobDefinitionID = int(time.time()) % 10000
        job.jobName = commands.getoutput('uuidgen')
        job.transformation = config['DEFAULT_TRF']
        job.destinationDBlock = datasetName
        job.destinationSE = destName
        job.currentPriority = 1000
        job.prodSourceLabel = 'user'
        job.computingSite = site
        job.cloud = 'RU'
        job.prodDBlock = "%s:%s.%s" % (scope, scope, job.jobName)

        job.jobParameters = '%s %s "%s"' %(release, distributive, parameters)

        params = {}
        _logger.debug('MoveData')
        ec = 0
        ec, uploaded_input_files = movedata(params=params, fileList=input_files, fromType=input_type, fromParams=input_params, toType='hpc', toParams={'dest': '/' + re.sub(':', '/', job.prodDBlock)})
        if ec != 0:
            _logger.error('Move data error: ' + ec[1])
            return

        for file in uploaded_input_files:
            fileIT = FileSpec()
            fileIT.lfn = file
            fileIT.dataset = job.prodDBlock
            fileIT.prodDBlock = job.prodDBlock
            fileIT.type = 'input'
            fileIT.scope = scope
            fileIT.status = 'ready'
            fileIT.GUID = commands.getoutput('uuidgen')
            job.addFile(fileIT)

        for file in output_files:
            fileOT = FileSpec()
            fileOT.lfn = file
            fileOT.destinationDBlock = job.prodDBlock
            fileOT.destinationSE = job.destinationSE
            fileOT.dataset = job.prodDBlock
            fileOT.type = 'output'
            fileOT.scope = scope
            fileOT.GUID = commands.getoutput('uuidgen')
            job.addFile(fileOT)


        fileOL = FileSpec()
        fileOL.lfn = "%s.log.tgz" % job.jobName
        fileOL.destinationDBlock = job.destinationDBlock
        fileOL.destinationSE = job.destinationSE
        fileOL.dataset = job.destinationDBlock
        fileOL.type = 'log'
        fileOL.scope = 'panda'
        job.addFile(fileOL)

        self.jobList.append(job)

        #submitJob
        o = self.submitJobs(self.jobList)
        x = o[0]

        #update PandaID
        conn = MySQLdb.connect(host=self.dbhost, db=self.dbname,
#                                        port=self.dbport, connect_timeout=self.dbtimeout,
                                        user=self.dbuser, passwd=self.dbpasswd)
        cur = conn.cursor()
        try:
            varDict = {}
            PandaID = int(x[0])
            varDict['id'] = jobid
            varDict['pandaId'] = PandaID

            sql = "UPDATE %s SET %s.pandaId=%s WHERE %s.id=%s" % (self.table_jobs, self.table_jobs, varDict['pandaId'], self.table_jobs, varDict['id'])
            cur.execute(sql, varDict)


        except:
            _logger.error('SENDJOB: Incorrect server response')
        try:
            conn.commit()
            return True
        except:
            _logger.error("commit error")
            return False



