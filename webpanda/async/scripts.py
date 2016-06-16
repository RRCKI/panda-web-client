# -*- coding: utf-8 -*-
import json

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.db.models import Container
from webpanda.db.models import DB
from webpanda.factory import create_celery_app
from webpanda.files.scripts import cloneReplica, linkReplica, copyReplica, uploadContainer
from webpanda.jobs.scripts import killJobs, send_job
from webpanda.pipelines.scripts import paleomix_main, paleomix_test


_logger = NrckiLogger().getLogger("async")

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


@celery.task
def cron_paleomix_main():
    return json.dumps(paleomix_main.run())


@celery.task
def cron_paleomix_test():
    return json.dumps(paleomix_test.run())


def prepareInputFiles(cont_id, se):
    _logger.debug('prepareInputFiles')
    # Initialize db
    s = DB().getSession()
    container = s.query(Container).filter(Container.id == cont_id).one()
    files = container.files
    tasks = []
    for f in files:
        replicas_len = f.replicas.count()
        if not replicas_len:
            raise Exception("No available replicas for file %s" % f.guid)
        replicas = f.replicas
        hasReplica = False
        _logger.debug('prepareInputFiles: file.lfn={}'.format(f.lfn))
        for replica in replicas:
            if replica.se == se and replica.status == 'ready':
                hasReplica = True
        _logger.debug('prepareInputFiles: replica.se={} replica.status={} hasReplica={}'.format(replica.se, replica.status, hasReplica))
        if not hasReplica:
            tasks.append(async_cloneReplica.s(replicas[0].id, se))
    s.close()
    return tasks