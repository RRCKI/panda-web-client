# -*- coding: utf-8 -*-
# """
#     webpanda.tasks
#     ~~~~~~~~~~~~~~
#     webpanda tasks module
# """
import json
#
from webpanda.factory import create_celery_app


#from webpanda.app import celery
from webpanda.files.scripts import cloneReplica, linkReplica, copyReplica, uploadContainer
from webpanda.jobs.scripts import killJobs, send_job

celery = create_celery_app()

@celery.task
def async_send_job(*args, **kwargs):
    jobid = kwargs.get('jobid', 0L)
    siteid = kwargs.get('siteid', 0L)
    if int(jobid) == 0:
        raise Exception('Illegal argument: jobid')
    if int(siteid) == 0:
        raise Exception('Illegal argument: siteid')

    return json.dumps(send_job(jobid, siteid))


@celery.task
def async_kill_job(pandaid):
    if int(pandaid) == 0:
        raise Exception('Illegal argument: jobid')

    return json.dumps(killJobs([pandaid]))


@celery.task
def async_cloneReplica(replicaid, se):
    return json.dumps(cloneReplica(replicaid, se))


@celery.task
def async_linkReplica(replicaid, dir):
    return json.dumps(linkReplica(replicaid, dir))


@celery.task
def async_copyReplica(replicaid, se, path):
    return json.dumps(copyReplica(replicaid, se, path))


@celery.task
def async_uploadContainer(ftp_dir, scope, cont_guid):
    res = None
    #try:
    res = uploadContainer(ftp_dir, scope, cont_guid)
    #except Exception as e:
    #raise async_uploadContainer.retry(countdown=60, exc=e, max_retries=5)
    return json.dumps(res)