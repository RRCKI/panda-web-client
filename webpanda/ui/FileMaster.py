from common import client_config
import json
from ui.Actions import movedata
from mq.MQ import MQ
from db.models import *
import os


class FileMaster:
    def __init__(self):
        self.table_files = 'files'

    def makeReplica(self, fileid, se):
        s = DB().getSession()
        file = s.query(File).filter(File.id == fileid).one()
        print file.id
        if file.status == 'registered':
            fromParams = {'token': file.token}
            dest = '/' + client_config.DEFAULT_SCOPE + '/' + file.guid
            toParams = {'dest': dest}
            ec, uploaded_input_files = movedata([], [file.lfn], file.se, fromParams, 'hpc', toParams)
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

    def cloneReplica(self, replicaid, se):
        pass

def mqCloneReplica(replicaid, se):
    routing_key = client_config.MQ_FILEKEY + '.clone'
    mq = MQ(host=client_config.MQ_HOST, exchange=client_config.MQ_EXCHANGE)
    # Create MQ request
    data = {}
    data['replicaid'] = replicaid
    data['se'] = se
    message = json.dumps(data)
    print '%s: %s %s' % ('mqCloneReplica', replicaid, se)
    mq.sendMessage(message, routing_key)

def mqMakeReplica(fileid, se):
    routing_key = client_config.MQ_FILEKEY + '.make'
    mq = MQ(host=client_config.MQ_HOST, exchange=client_config.MQ_EXCHANGE)
    # Create MQ request
    data = {}
    data['fileid'] = fileid
    data['se'] = se
    message = json.dumps(data)
    print '%s: %s %s' % ('mqMakeReplica', fileid, se)
    mq.sendMessage(message, routing_key)