# -*- coding: utf-8 -*-
from base64 import b64encode
import re
import commands
from datetime import datetime
from flask import current_app

from webpanda.core import WebpandaError
from webpanda.files import Container
from webpanda.jobs import Job
from webpanda.services import tasks_, conts_, jobs_, sites_, distrs_, users_
from webpanda.async import async_send_job
from webpanda.fc.Client import Client as fc


def check_input(task):
    # Get containers
    input_cont = conts_.get(task.input)
    #output_cont = conts_.get(task.output)

    # Check input files
    files_template_list = task.task_type.ifiles_template.split(',')

    for item in input_cont.files:
        f = item.file

        for file_template in files_template_list:

            m = re.match(file_template, f.lfn)
            if m is not None:
                files_template_list.remove(file_template)
    #if len(files_template_list)>0:
    #   raise WebpandaDebug("Input files not found in input container")
    return len(files_template_list)


def run(task, metod):
    try:
        if task.status != 'sent':
            return False
        #    raise WebpandaError('Illegal task status to start')

        # Change task state to 'running'
        task.status = 'preparing'
        task.modification_time = datetime.utcnow()
        tasks_.save(task)

        # Custom payload
        if metod == 'init_task':
            payload1(task)
        if metod == 'split_task':
            payload2(task)
        #...

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


def send_job_(task, container, script):
    #### Send PanDA jobs
    task.tag = "task." + commands.getoutput('uuidgen')
    tasks_.save(task)

    # Get default ComputingElement
    site = sites_.first(ce=current_app.config['DEFAULT_CE'])
    if site is None:
        raise WebpandaError("ComputingElement not found")
    # Get distributive
    distr = distrs_.get(1)

    # Define jobs
    job = Job()
    job.pandaid = None
    job.status = 'pending'
    job.owner = users_.get(task.owner_id)
    job.params = b64encode(script)
    job.distr = distr
    job.container = container
    job.creation_time = datetime.utcnow()
    job.modification_time = datetime.utcnow()
    #job.ninputfiles = 0
    #job.noutputfiles = 0
    job.corecount = 1
    job.tags = task.tag
    jobs_.save(job)

    # Async sendjob
    async_send_job.s(jobid = job.id, siteid = site.id)


def payload1(task):
    # init
    return True


def payload2(task):
    """
    split_task
    Split input *.1.fastq and *.2.fastq into 'rn' pieces=
    run panda /bin/bash split.sh
    -Register results into output_cont
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


    # Get container
    container = Container()
    container.guid = task.tag + ".0"
    conts_.save(container)

    rn = 0
    # Add input files to container
    files_template_list = task_type.ifiles_template.split(',')
    for item in input_cont.files:
        f = item.file
        # TODO deal with fastq.bz2 input files
        if rn == 0:
            if f.lfn.endswith('fastq'):
                rn = getn(f.fsize)
            elif f.lfn.endswith('fastq.bz2'):
                rn = getn2(f.fsize)

        for file_template in files_template_list:
            # TODO: Change file template here
            m = re.match(file_template, f.lfn)
            if m is not None:
                # Register file in container
                fc.reg_file_in_cont(f, container, 'input')

    # Prepare trf script
    script = task.task_type.trf_template
    #TODO script
    #script="/bin/bash /home/users/poyda/lustre/swp/split.sh " + str(rn)

    send_job_(task, container, script)

    return True


def getn(fsize):
    # TO_DO deal with fastq.bz2 input files
    basen = 1610612736  #1.5G - we has 3.6G for small biotask, and 175G for 135 subtasks for bigbiotask
    basedst = 2
    rn = 0
    n = int(fsize // basen)
    if n > 10 and n < 150:
        rn = n
    elif n >= 150:
        rn = 200
    elif n >= 1 and n <= 10:
        rn = n * 2
    else:
        rn = 4
        while basedst > 0:
            basen = int(basen // 2)
            n = int(fsize // basen)
            if n > 10:
                rn = n
                break
            basedst -= 1
    return rn

def getn2(fsize):
    # TO_DO deal with fastq.bz2 input files
    basen = 240*1024*1024  #240Mb - bz2 ratio from x6 to x5 - we has 650M for small biotask, and 240M for 135 subtasks for ??G bigbiotask
    basedst = 2
    rn = 0
    n = int(fsize // basen)
    if n > 10 and n < 150:
        rn = n
    elif n >= 150:
        rn = 200
    elif n >= 1 and n <= 10:
        rn = n * 2
    else:
        rn = 4
        while basedst > 0:
            basen = int(basen // 2)
            n = int(fsize // basen)
            if n > 10:
                rn = n
                break
            basedst -= 1
    return rn