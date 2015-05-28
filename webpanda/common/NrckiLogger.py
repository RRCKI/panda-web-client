import os
import logging

from common import client_config

# setup logger
_formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')

class NrckiLogger:
    def __init__(self):
        self.logdir = os.path.join(client_config.basedir, client_config.LOG_DIR)

    def getLogger(self, name):
        _logger = logging.getLogger(name)
        hdlr = logging.FileHandler(os.path.join(self.logdir, 'webpanda-%s.log' % name))
        formatter = logging.Formatter('%(asctime)s %(name)s [%(levelname)s]: %(message)s')
        hdlr.setFormatter(formatter)
        _logger.addHandler(hdlr)
        _logger.setLevel(logging.DEBUG)
        return _logger