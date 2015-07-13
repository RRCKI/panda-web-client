# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from api import app, manager
import os
if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
    #app.run(debug = True)
    manager.run()