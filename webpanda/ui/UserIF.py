from webpanda.common.NrckiLogger import NrckiLogger

_logger = NrckiLogger().getLogger("UserIF")

class UserIF:
    def __init__(self):
        pass

    def getJobStatus(self, ids):
        import userinterface.Client as Client
        s,o = Client.getJobStatus(ids)
        result = {}
        if s != 0:
            _logger.error('Error response code: %s %s' %(str(s), str(o)))
            return result
        for x in o:
            result[x.PandaID] = x.jobStatus
        return result

    def killJobs(self, ids, code=None, verbose=False):
        """Kill jobs. Normal users can kill only their own jobs.
        People with production VOMS role can kill any jobs.
        Running jobs are killed when next heartbeat comes from the pilot.
        Set code=9 if running jobs need to be killed immediately.

           args:
               ids: the list of PandaIDs
               code: specify why the jobs are killed
                     2: expire
                     3: aborted
                     4: expire in waiting
                     7: retry by server
                     8: rebrokerage
                     9: force kill
                     50: kill by JEDI
                     91: kill user jobs with prod role
               verbose: set True to see what's going on
           returns:
               status code
                     0: communication succeeded to the panda server
                     255: communication failure
               the list of clouds (or Nones if tasks are not yet assigned)
        """
        import userinterface.Client as Client
        s,o = Client.killJobs(ids, code=code, verbose=verbose)

# Singleton
userIF = UserIF()
del UserIF


def getJobStatus(req, ids):
    userIF.getJobStatus(ids)

def killJobs(req, ids):
    userIF.killJobs(ids)