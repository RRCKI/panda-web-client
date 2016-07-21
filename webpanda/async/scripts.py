# -*- coding: utf-8 -*-
import json

from webpanda.async import celery
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.core import WebpandaError
from webpanda.files.scripts import cloneReplica, linkReplica, copyReplica, uploadContainer
from webpanda.jobs.scripts import killJobs, send_job
from webpanda.services import conts_


_logger = NrckiLogger().getLogger("async")


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


def prepareInputFiles(cont_id, se):
    _logger.debug('prepareInputFiles')
    container = conts_.get(cont_id)
    cc = container.files
    tasks = []
    for c in cc:
        f = c.file
        replicas_len = f.replicas.count()
        if not replicas_len:
            raise WebpandaError("No available replicas for file %s" % f.guid)
        replicas = f.replicas
        hasReplica = False
        _logger.debug('prepareInputFiles: file.lfn={}'.format(f.lfn))
        for replica in replicas:
            if replica.se == se and replica.status == 'ready':
                hasReplica = True
        _logger.debug('prepareInputFiles: replica.se={} replica.status={} hasReplica={}'.format(replica.se, replica.status, hasReplica))
        if not hasReplica:
            tasks.append(async_cloneReplica.s(replicas[0].id, se))
    return tasks