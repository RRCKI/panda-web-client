# -*- coding: utf-8 -*-
# """
#     webpanda.tasks
#     ~~~~~~~~~~~~~~
#     webpanda tasks module
# """
import json
#
# from webpanda.factory import create_celery_app
#
from webpanda.ui.FileMaster import FileMaster
from webpanda.ui.JobMaster import JobMaster
#
# celery = create_celery_app()
from webpanda.app import celery
#
@celery.task
def send_job(*args, **kwargs):
    jobid = kwargs.get('jobid', 0L)
    siteid = kwargs.get('siteid', 0L)
    if int(jobid) == 0:
        raise Exception('Illegal argument: jobid')
    if int(siteid) == 0:
        raise Exception('Illegal argument: siteid')
    jm = JobMaster()

    return json.dumps(jm.send_job(jobid, siteid))


@celery.task
def kill_job(pandaid):
    if int(pandaid) == 0:
        raise Exception('Illegal argument: jobid')
    jm = JobMaster()

    return json.dumps(jm.killJobs([pandaid]))


@celery.task
def cloneReplica(replicaid, se):
    fm = FileMaster()
    return json.dumps(fm.cloneReplica(replicaid, se))


@celery.task
def linkReplica(replicaid, dir):
    fm = FileMaster()
    return json.dumps(fm.linkReplica(replicaid, dir))


@celery.task
def copyReplica(replicaid, se, path):
    fm = FileMaster()
    return json.dumps(fm.copyReplica(replicaid, se, path))


@celery.task
def async_uploadContainer(ftp_dir, scope, cont_guid):
    fm = FileMaster()
    res = None
    #try:
    res = fm.uploadContainer(ftp_dir, scope, cont_guid)
    #except Exception as e:
    #raise async_uploadContainer.retry(countdown=60, exc=e, max_retries=5)
    return json.dumps(res)