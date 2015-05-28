import pika
import json
from common.NrckiLogger import NrckiLogger
from common import client_config

_logger = NrckiLogger().getLogger("MQ")


class MQ:
    def __init__(self, host=client_config.MQ_HOST, exchange='default'):
        self.exchange = exchange
        self.host = host

    def getClient(self, server):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=server))
        channel = connection.channel()
        return channel, connection

    def sendMessage(self, message, routing_key):
        channel, connection = self.getClient(self.host)

        channel.exchange_declare(exchange=self.exchange,
                                 type='topic')

        channel.basic_publish(exchange=self.exchange,
                              routing_key=routing_key,
                              body=message,
                              properties=pika.BasicProperties(
                                 delivery_mode=2, # make message persistent
                              ))
        connection.close()

    def startJobConsumer(self):
        from ui.JobMaster import JobMaster

        binding_keys = [client_config.MQ_JOBKEY + '.#']

        channel, connection = self.getClient(self.host)

        channel.exchange_declare(exchange=self.exchange,
                                     type='topic')

        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        if not binding_keys:
            raise AttributeError('No keys for queue')

        for key in binding_keys:
            channel.queue_bind(exchange=self.exchange,
                               queue=queue_name,
                               routing_key=key)

        def callback(ch, method, properties, body):
            data = json.loads(body)
            #TODO message checking
            JobMaster().run(data)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(callback, queue=queue_name)

        channel.start_consuming()

    def startFileConsumer(self):
        from ui.FileMaster import FileMaster

        binding_keys = [client_config.MQ_FILEKEY + '.#']

        channel, connection = self.getClient(self.host)

        channel.exchange_declare(exchange=self.exchange,
                                     type='topic')

        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        if not binding_keys:
            raise AttributeError('No keys for queue')

        for key in binding_keys:
            channel.queue_bind(exchange=self.exchange,
                               queue=queue_name,
                               routing_key=key)

        def callback(ch, method, properties, body):
            data = json.loads(body)
            fileid = data['fileid']
            se = data['se']
            #TODO message checking
            FileMaster().makeReplica(fileid, se)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(callback, queue=queue_name)

        channel.start_consuming()