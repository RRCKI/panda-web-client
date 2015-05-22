import sys
from common.NrckiLogger import NrckiLogger
from mq.MQ import MQ
_logger = NrckiLogger().getLogger("comsumer")

if __name__ == '__main__':

    _logger.debug(' '.join(sys.argv))

    keys = sys.argv[1:]

    if len(keys) == 1 and keys[0] == 'method.sendjob':
        mq = MQ(host='localhost', exchange='lsm')
        mq.startSendJobConsumer()
