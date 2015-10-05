import pika
import sys

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.common import client_config

_logger = NrckiLogger().getLogger("MQ")

connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=client_config.MQ_HOST))
channel = connection.channel()

channel.exchange_declare(exchange=client_config.MQ_EXCHANGE,
                         type='topic')

result = channel.queue_declare(exclusive=True)
queue_name = result.method.queue

binding_keys = [client_config.MQ_EXCHANGE + '.#']
if not binding_keys:
    sys.exit(1)

for binding_key in binding_keys:
    channel.queue_bind(exchange=client_config.MQ_EXCHANGE,
                       queue=queue_name,
                       routing_key=binding_key)

def callback(ch, method, properties, body):
    _logger.debug(" [x] %r:%r" % (method.routing_key, body,))

channel.basic_consume(callback,
                      queue=queue_name,
                      no_ack=True)

channel.start_consuming()