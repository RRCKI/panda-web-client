# -*- coding: utf-8 -*-
from webpanda.services import pipelines_, tasks_


def run():
    print "main started"
    pipelines_init = pipelines_.find(current_state='init')
    for pipeline in pipelines_init:
        task = pipeline.init_task
        if task.status == 'defined':
            task.status = 'pending'
            tasks_.save(task)