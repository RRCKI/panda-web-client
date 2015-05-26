from common import client_config
from ui.Actions import movedata
from db.models import *
import os


class FileMaster:
    def __init__(self):
        self.table_files = 'files'

    def makeReplica(self, fileid, se, params):
        s = DB().getSession()
        file = s.query(File).filter(File.id == fileid).one()
        print file.id
        if file.status == 'registered':
            fromParams = {'token': file.token}
            dest = '/' + client_config.DEFAULT_SCOPE + '/' + params['dir']
            toParams = {'dest': dest}
            # ec, uploaded_input_files = movedata([], [file.lfn], file.se, fromParams, 'hpc', toParams)
            ec = 0
            if ec == 0:
                replica = Replica()
                replica.se = se
                replica.status = 'ready'
                replica.lfn = os.path.join(dest, file.lfn.split('/')[-1])
                file.replicas.append(replica)
                s.add(replica)
                s.commit()
                s.add(file)
                s.commit()
        s.close()
        return ec

    def cloneReplica(self, replicaid, se, params):
        pass