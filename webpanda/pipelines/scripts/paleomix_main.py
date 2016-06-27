# -*- coding: utf-8 -*-
from datetime import datetime
from flask_login import current_user
from webpanda.core import WebpandaError
from webpanda.pipelines.scripts import paleomix_init
from webpanda.services import pipelines_, tasks_, jobs_, task_types_
from webpanda.tasks import Task


def run():
    print "main started"

    # Fetch pipelines (init state)
    pipelines = pipelines_.all()
    for pipeline in pipelines:

        # Fetch task object
        current_task_id = getattr(pipeline, pipeline.current_task + "_id")
        current_task = tasks_.get(current_task_id)

        if current_task.status == 'defined':

            #TODO: Run async regime
            if current_task.task_type.method == 'init_task':
                paleomix_init.run(current_task)


def check_running_tasks():
    print "check tasks started"

    # Get tasks in running state
    tasks = tasks_.find(status='running')
    for task in tasks:
        # Check if tag defined
        if task.tag is not None and task.tag != "":
            # Check failed Panda jobs
            jobs = jobs_.find(tags=task.tag, status='failed')
            if jobs.count > 0:
                task.status = 'failed'
                tasks_.save(task)

            # Check failed Panda jobs
            jobs = jobs_.find(tags=task.tag, status='canceled')
            if jobs.count > 0:
                task.status = 'canceled'
                tasks_.save(task)

            # Check finished Panda jobs
            jobs = jobs_.find(tags=task.tag, status='finished')
            jobs_all = jobs_.find(tags=task.tag)
            if jobs.count == jobs_all.count:
                task.status = 'finished'
                tasks_.save(task)
        else:
            # If tag is not defined
            task.status = 'finished'
            tasks_.save(task)


def check_next_task():
    print "check_next_task started"

    # Get tasks in finished state
    tasks = tasks_.find(status='finished')

    for task in tasks:
        # Get pipeline of task
        type_name = task.task_type.method
        pipeline = pipelines_.first({type_name + '_id': task.id})

        # If pipeline not found
        if pipeline is None:
            task.status = 'finished_no_pipeline'
            tasks_.save(task)

        # Get next task type id
        next_task_type_id = pipeline.next_task_type()

        # Check if last task
        if next_task_type_id is None:
            pipeline.status = 'finished'
            pipelines_.save(pipeline)
            return True

        # Get next task type
        next_task_type = task_types_.get(next_task_type_id)

        # If next task exists
        next_task = Task()
        next_task.owner_id = current_user.id
        next_task.task_type_id = next_task_type_id
        next_task.creation_time = datetime.utcnow()
        next_task.modification_time = datetime.utcnow()
        next_task.status = 'defined'
        next_task.input = task.input
        next_task.output = task.output
        tasks_.save(next_task)

        # Set task/pipeline relation
        pipeline.current_state = next_task_type.method
        setattr(pipeline, next_task_type.method + "_id", next_task.id)
        pipelines_.save(pipeline)

