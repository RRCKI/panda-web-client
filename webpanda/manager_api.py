# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from webpanda.api import app, manager


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
    #app.run(debug = True)
    manager.run()