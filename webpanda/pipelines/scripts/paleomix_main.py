# -*- coding: utf-8 -*-
from datetime import datetime
from webpanda.pipelines.scripts import paleomix_init, paleomix_split, paleomix
from webpanda.services import pipelines_, tasks_, jobs_, task_types_, conts_
from webpanda.tasks import Task
from webpanda.fc.Client import Client as fc
from webpanda.pipelines import client as pclient
from webpanda.core import WebpandaError


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
        current_task = pclient.get_current_task(pipeline)

        if current_task.status == 'defined':
            # Run task if defined
            current_task.status = 'sent'
            tasks_.save(current_task)

            #TODO: Run async regime
            if current_task.task_type.method == 'init_task':
                paleomix_init.run(current_task.id)
            elif current_task.task_type.method == 'split_task':
                paleomix_split.run(current_task.id)

def run2():
    """
    Starts current defined task
    :return:
    """
    print "main started"

    # Fetch pipelines (init state)
    #TODO add SQL filter on status if possible
    pipelines = pipelines_.all()
    for pipeline in pipelines:
        # Check if finished
        if pipeline.status in ['finished', 'failed', 'cancelled']:
            continue

        # By default set init_task state
        #TODO can do it at pipeline creation time? We`ve done apparently nothing else since that.
        if pipeline.status == 'starting':
            pipeline.status = 'running'
            pipeline.current_state = '0'
            pipelines_.save(pipeline)

        # Fetch task object
        current_task = pclient.get_current_task(pipeline)

        if current_task is None:
            return WebpandaError('Illegal task ID')

        if current_task.status == 'defined':
            # Do some checks if it usefull - or we have all files already, or there would be never enough of them.
            if paleomix.check_input(current_task) != 0:
                continue
            # Run task if defined
            current_task.status = 'sent'
            tasks_.save(current_task)

            #TO_DO: Run async regime
            paleomix.run(current_task) # we already get task from id. Not need to obtain again, is it?
        #TODO if current_task.status != 'defined' we can operate some steps from 2 others 'cron_tasks'


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
                return False

            # Check failed Panda jobs
            jobs = jobs_.find(tags=task.tag, status='canceled')
            if jobs.count > 0:
                task.status = 'cancelled'
                task.modification_time = datetime.utcnow()
                tasks_.save(task)
                return False

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
                            # Register file in container
                            fc.reg_file_in_cont(f.file, cont, 'intermediate')

                # Change task status
                task.status = 'finished'
                task.modification_time = datetime.utcnow()
                tasks_.save(task)
                return True
        else:
            # If tag is not defined
            task.status = 'finished'
            task.modification_time = datetime.utcnow()
            tasks_.save(task)
    return True


def check_next_task2():
    """
    Checks finished task and starts next one
    Will work with numbered next_task
    :return:
    """

    # Get all pipelines
    pipelines = pipelines_.find(status='running')
    for pipeline in pipelines:
        current_task = pclient.get_current_task(pipeline)

        if current_task.status == 'finished':
            # Get next_task
            next_task = pclient.get_next_task(pipeline)

            # Check if last task
            if pclient.is_finish_task(next_task):
                pipeline.status = 'finished'
                pipelines_.save(pipeline)
                continue

        elif current_task.status == 'failed':
            #TODO: What to do if failed?
            pipeline.status = 'failed'
            pipelines_.save(pipeline)
            return True
        elif current_task.status == 'cancelled':
            #TODO: What to do if cancelled?
            #TODO: Who or by whom? If by system - resubmit, if by user -nothing?
            pipeline.status = 'cancelled'
            pipelines_.save(pipeline)
            return True