# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from app import app
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
app.run(debug = True)