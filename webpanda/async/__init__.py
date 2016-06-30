"""
    webpanda.async
    ~~~~~~~~~~~~~~
    webpanda async module
"""
from webpanda.factory import create_celery_app

celery = create_celery_app()

from .scripts import *
from .pipelines import *
