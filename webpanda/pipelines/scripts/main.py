# -*- coding: utf-8 -*-
from datetime import datetime
from webpanda.pipelines.scripts import paleomix
from webpanda.services import pipelines_, tasks_, jobs_, conts_
from webpanda.fc import client as fc
from webpanda.pipelines import client as pclient
from webpanda.core import WebpandaError


def run():
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

        # Fetch task object
        current_task = pclient.get_current_task(pipeline)

        if current_task is None:
            return WebpandaError('Illegal task ID')

        if current_task.status == 'failed':
            #TODO: What to do if failed?
            pipeline.status = 'failed'
            current_task.modification_time = datetime.utcnow()
            pipelines_.save(pipeline)
            continue

        if current_task.status == 'cancelled':
            #TODO: What to do if cancelled?
            #TODO: Who or by whom? If by system - resubmit, if by user -nothing?
            pipeline.status = 'cancelled'
            current_task.modification_time = datetime.utcnow()
            pipelines_.save(pipeline)
            continue

        if current_task.status == 'finished':
            # Get next_task
            current_task = pclient.get_next_task(pipeline)

        if current_task.status == 'defined':
            if current_task.task_type.method == 'start':

                # Do some general pipeline checks

                current_task.status = 'finished'
                current_task.modification_time = datetime.utcnow()
                tasks_.save(current_task)
                continue
            elif current_task.task_type.method == 'finish':
                current_task.status = 'finished'
                current_task.modification_time = datetime.utcnow()
                tasks_.save(current_task)

                # Process system finish task
                pipeline.status = 'finished'
                pipeline.modification_time = datetime.utcnow()
                pipelines_.save(pipeline)
                continue
            else:
                # Process system start task
                # Do some checks if it usefull - or we have all files already, or there would be never enough of them.
                if not paleomix.has_input(current_task):
                    current_task.status = "failed"
                    current_task.modification_time = datetime.utcnow()
                    current_task.comment = "Input files check failed"
                    tasks_.save(current_task)

                    pipeline.status = 'failed'
                    pipeline.modification_time = datetime.utcnow()
                    pipelines_.save(pipeline)
                    continue

                # Run task if defined
                current_task.status = 'sent'
                tasks_.save(current_task)

                #TO_DO: Run async regime
                paleomix.run(current_task, current_task.task_type.method) # we already get task from id. Not need to obtain again, is it?
                # if we use async run, all params must be serializable (BaseQuery is not)
                continue


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
                task.comment = "Failed task due to {n} failed jobs".format(n=jobs.count)
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
