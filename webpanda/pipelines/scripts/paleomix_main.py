# -*- coding: utf-8 -*-
from datetime import datetime
from webpanda.files import Catalog
from webpanda.pipelines.scripts import paleomix_init, paleomix_split
from webpanda.services import pipelines_, tasks_, jobs_, task_types_, conts_, catalog_
from webpanda.tasks import Task


def run():
    """
    Starts current defined task
    :return:
    """
    print "main started"

    # Fetch pipelines (init state)
    pipelines = pipelines_.all()
    for pipeline in pipelines:
        # Check if finished
        if pipeline.status in ['finished', 'failed', 'cancelled']:
            continue

        # By default set init_task state
        if pipeline.status == 'starting':
            pipeline.status = 'running'
            pipeline.current_state = 'init_task'
            pipelines_.save(pipeline)

        # Fetch task object
        current_task = tasks_.get(pipeline.get_current_task_id())

        if current_task.status == 'defined':
            # Run task if defined
            current_task.status = 'sent'
            tasks_.save(current_task)

            #TODO: Run async regime
            if current_task.task_type.method == 'init_task':
                paleomix_init.run(current_task.id)
            elif current_task.task_type.method == 'split_task':
                paleomix_split.run(current_task.id)


def check_running_tasks():
    """
    Checks PanDA jobs statuses for all running tasks
    :return:
    """
    # Get tasks in running state
    tasks = tasks_.find(status='running')
    for task in tasks:
        # Check if tag defined
        if task.tag is not None and task.tag != "":
            # Check failed Panda jobs
            jobs = jobs_.find(tags=task.tag, status='failed')
            if jobs.count > 0:
                task.status = 'failed'
                task.modification_time = datetime.utcnow()
                tasks_.save(task)

            # Check failed Panda jobs
            jobs = jobs_.find(tags=task.tag, status='canceled')
            if jobs.count > 0:
                task.status = 'canceled'
                task.modification_time = datetime.utcnow()
                tasks_.save(task)

            # Check finished Panda jobs
            jobs = jobs_.find(tags=task.tag, status='finished')
            jobs_all = jobs_.find(tags=task.tag)
            if jobs.count == jobs_all.count:
                # Register files from jobs into task container
                cont = conts_.get(task.input)
                for job in jobs:
                    files_catalog = job.container.files
                    for f in files_catalog:
                        if f.type == 'output':
                            c = Catalog()
                            c.file = f.file
                            c.cont = cont
                            c.type = 'intermediate'
                            catalog_.save(c)

                # Change task status
                task.status = 'finished'
                task.modification_time = datetime.utcnow()
                tasks_.save(task)
        else:
            # If tag is not defined
            task.status = 'finished'
            task.modification_time = datetime.utcnow()
            tasks_.save(task)
    return True


def check_next_task():
    """
    Checks finished task and starts next one
    :return:
    """

    # Get all pipelines
    pipelines = pipelines_.find(status='running')
    for pipeline in pipelines:
        current_task = tasks_.get(pipeline.get_current_task_id())

        if current_task.status == 'finished':
            pipeline_type = pipeline.pipeline_type

            # Get next task type id
            next_task_type_id = pipeline_type.get_next_task_type_id(current_task.task_type.method)

            # Check if last task
            if next_task_type_id is None:
                pipeline.current_state = None
                pipeline.status = 'finished'
                pipelines_.save(pipeline)
                continue

            # Get next task type
            next_task_type = task_types_.get(next_task_type_id)

            # If next task exists
            next_task = Task()
            next_task.owner_id = pipeline.owner_id
            next_task.task_type_id = next_task_type_id
            next_task.creation_time = datetime.utcnow()
            next_task.modification_time = datetime.utcnow()
            next_task.status = 'defined'
            next_task.input = current_task.input
            next_task.output = current_task.output
            tasks_.save(next_task)

            # Set task/pipeline relation
            pipeline.current_state = next_task_type.method
            setattr(pipeline, next_task_type.method + "_id", next_task.id)
            pipelines_.save(pipeline)
        elif current_task.status == 'failed':
            #TODO: What to do if failed?
            pipeline.current_state = None
            pipeline.status = 'failed'
            pipelines_.save(pipeline)
            return True
        elif current_task.status == 'cancelled':
            #TODO: What to do if cancelled?
            pipeline.current_state = None
            pipeline.status = 'cancelled'
            pipelines_.save(pipeline)
            return True

