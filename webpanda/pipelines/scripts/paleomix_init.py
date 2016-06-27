# -*- coding: utf-8 -*-
from webpanda.core import WebpandaError
from webpanda.services import tasks_


def run(task):
    try:
        if task.status != 'defined':
            raise WebpandaError('Illegal task status to start')

        # Change task state to 'running'
        task.status = 'preparing'
        tasks_.save(task)

        # Do all job
        # Start PanDA jobs

        # Change task state to 'finished'
        task.status = 'running'
        tasks_.save(task)
        return True

    except WebpandaError as e:
        # Change task state to 'finished'
        task.status = 'failed'
        task.comment = e.msg
        tasks_.save(task)
        return False
