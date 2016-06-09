# -*- coding: utf-8 -*-
"""
    webpanda.jobs
    ~~~~~~~~~~~~~~~~~
    webpanda jobs package
"""

from webpanda.core import Service
from webpanda.jobs.models import Job, Distributive, Site


class JobService(Service):
    __model__ = Job

class DistrService(Service):
    __model__ = Distributive


class SiteService(Service):
    __model__ = Site
