import sys
from common.NrckiLogger import NrckiLogger
from mq.MQ import MQ
from common import client_config
_logger = NrckiLogger().getLogger("comsumer")

if __name__ == '__main__':

    _logger.debug(' '.join(sys.argv))

    keys = sys.argv[1:]

    if len(keys) == 1 and keys[0] == 'jobs':
        mq = MQ(host=client_config.MQ_HOST, exchange=client_config.MQ_EXCHANGE)
        mq.startJobConsumer()

    if len(keys) == 1 and keys[0] == 'files':
        mq = MQ(host=client_config.MQ_HOST, exchange=client_config.MQ_EXCHANGE)
        mq.startFileConsumer()
