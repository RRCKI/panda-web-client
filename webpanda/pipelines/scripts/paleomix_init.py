# -*- coding: utf-8 -*-
import re
import commands
from datetime import datetime
from flask import current_app

from webpanda.core import WebpandaError
from webpanda.files import Container, Catalog
from webpanda.jobs import Job
from webpanda.services import tasks_, conts_, jobs_, sites_, distrs_, catalog_
from webpanda.async import async_send_job


def run(task_id):
    try:
        task = tasks_.get(task_id)
        if task is None:
            return WebpandaError('Illegal task ID')

        if task.status != 'sent':
            raise WebpandaError('Illegal task status to start')

        # Change task state to 'running'
        task.status = 'preparing'
        task.modification_time = datetime.utcnow()
        tasks_.save(task)

        # Custom payload
        payload(task)

        # Change task state to 'finished'
        task.status = 'running'
        task.modification_time = datetime.utcnow()
        tasks_.save(task)
        return True

    except WebpandaError as e:
        # Change task state to 'finished'
        task.status = 'failed'
        task.modification_time = datetime.utcnow()
        task.comment = e.msg
        tasks_.save(task)
        return False


def payload(task):
    """
    Checks if necessary files in input container
    :param task:
    :return:
    """
    #### Prepare
    # Check type of task
    task_type = task.task_type
    if task_type.id != 2:
        raise WebpandaError("Illegal task_type.id")

    # Get containers
    input_cont = conts_.get(task.input)
    output_cont = conts_.get(task.output)

    # Check input files
    files_template_list = task_type.ifiles_template.split(',')

    for item in input_cont.files:
        f = item.file

        for file_template in files_template_list:
            m = re.match(file_template, f.lfn)
            if m is None:
                raise WebpandaError("Input files not found in input container")

    #### Send PanDA jobs
    task.tag = "task." + commands.getoutput('uuidgen')
    tasks_.save(task)

    # Get default ComputingElement
    site = sites_.first(ce=current_app.config['DEFAULT_CE'])

    # Get distributive
    distr = distrs_.get(1)

    for i in xrange(2):
        # Get container
        container = Container()
        container.guid = task.tag + "." + str(i)
        conts_.save(container)

        # Add input files to container
        for item in input_cont.files:
            f = item.file

            for file_template in files_template_list:
                # TODO: Change file template here
                m = re.match(file_template, f.lfn)
                if m is not None:
                    c = Catalog()
                    c.cont = container
                    c.file = f
                    c.type = 'input'
                    catalog_.save(c)

        # Define jobs
        job = Job()
        job.pandaid = None
        job.status = 'pending'
        job.owner = g.user
        job.params = "echo 123"
        job.distr = distr
        job.container = container
        job.creation_time = datetime.utcnow()
        job.modification_time = datetime.utcnow()
        job.ninputfiles = 0
        job.noutputfiles = 0
        job.corecount = 1
        job.tags = task.tag
        jobs_.save(job)

        # Async sendjob
        async_send_job.s(jobid=job.id, siteid=site.id)

    return True
