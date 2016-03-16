# -*- coding: utf-8 -*-
"""
    webpanda.jobs
    ~~~~~~~~~~~~~~~~~
    webpanda jobs package
"""

from webpanda.core import Service
from webpanda.jobs.models import Job


class JobService(Service):
    __model__ = Job
