# -*- coding: utf-8 -*-
from base64 import b64encode
from flask import current_app
import re
import commands
from datetime import datetime

from webpanda.core import WebpandaError
from webpanda.files import Container
from webpanda.jobs import Job
from webpanda.pipelines.scripts import logger
from webpanda.services import tasks_, conts_, users_, jobs_, sites_, files_
from webpanda.fc import client as fc
from webpanda.async import async_send_job


def has_input(task):
    logger.debug("has_input: Start " + str(task.id))
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
    retval = len(files_template_list) == 0
    logger.debug("has_input: " + str(retval))
    return retval


def send_job_(task, container, script):
    """
    Prepares a job for task with container and trf script
    :param task: Task obj to append a job
    :param container: Container obj for job
    :param script: str Trf script
    :return: True
    """
    # Get default ComputingElement
    site = sites_.first(ce=current_app.config['DEFAULT_CE'])
    if site is None:
        raise WebpandaError("ComputingElement not found")

    # Get distributive
    distr = task.task_type.distr

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
    async_send_job.delay(jobid=job.id, siteid=site.id)
    return True


def run(task):
    try:
        method = task.task_type.method
        if task.status != 'sent':
            return False
        #    raise WebpandaError('Illegal task status to start')

        # Change task state to 'running'
        task.status = 'preparing'
        task.modification_time = datetime.utcnow()
        tasks_.save(task)

        # Custom payload
        if method == 'init_task':
            payload1(task)
        elif method == 'split_task':
            payload2(task)
        elif method == 'run1_task':
            payload3(task)
        else:
            raise WebpandaError("Task payload error: method not found")

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


def payload1(task):
    # Init
    logger.debug("payload1: Start")
    return True


def payload2(task):
    """
    split_task
    Split input *.1.fastq and *.2.fastq into 'rn' pieces=
    run panda /bin/bash split.sh
    :param task:
    :return:
    """
    logger.debug("payload2: Start")

    #### Prepare
    # Check type of task
    task_type = task.task_type
    if task_type.id != 1:
        raise WebpandaError("Illegal task_type.id")

    logger.debug("payload2: tasktype " + str(task_type.id))

    # Get user
    user = users_.get(task.owner_id)
    logger.debug("payload2: user " + str(user.id))

    # Get containers
    input_cont = conts_.get(task.input)
    #TODO do smth with output container?
    output_cont = conts_.get(task.output)

    task.tag = "task." + commands.getoutput('uuidgen')
    tasks_.save(task)
    logger.debug("payload2: tag " + task.tag)

    # Get container
    container = Container()
    container.guid = task.tag + ".0"
    conts_.save(container)
    logger.debug("payload2: cont " + container.guid)

    script_add = ""

    rn = 0
    # Add input files to container
    files_template_list = task_type.ifiles_template.split(',')
    for item in input_cont.files:
        f = item.file
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
                if f.lfn.endswith('.fastq'):
                    for fi in gen_sfx(f.lfn[:-5], rn, '.fastq'):
                        fc.reg_file_in_cont_byname(user, fi, container, 'output')
                if f.lfn.endswith('.fastq.bz2'):
                    for fi in gen_sfx(f.lfn[:-9], rn, '.fastq'):
                        fc.reg_file_in_cont_byname(user, fi, container, 'output')
                if f.lfn.endswith('.fasta'):
                    fn=f.lfn+'.'
                    fc.reg_file_in_cont_byname(user, fn[:-6]+'dict', container, 'output')
                    # itert: validated file has null size
                    #for sfx in ('amb','ann','bwt','fai','pac','sa','validated'):
                    for sfx in ('amb','ann','bwt','fai','pac','sa', 'validated'):
                        fc.reg_file_in_cont_byname(user, fn+sfx, container, 'output')

                    script_add += "; echo 123 > ../{fname}".format(fname=fn+"validated")

    logger.debug("payload2: reg Makefile")
    #reg additional output
    for fi in gen_sfx('Makefile', rn, '.yaml'):
        fc.reg_file_in_cont_byname(user, fi, container, 'output')

    guids = ["web.it_4b7d4757-9ba4-4ed7-8bc0-6edb8bcc68d2",
             "web.it_3bc78e60-241b-418a-a631-2461d4ba1977",
             "web.it_1b88049e-463b-4b4f-8454-9587301a53e5",
             "web.it_a02271ea-8a9b-42f3-add2-ed6d0f9ff07e",
             "web.it_61bb7c80-e53c-4641-88b0-fbd16b0f3d56",
             "web.it_3930f596-25ea-49b0-8943-7a83c84c7940",
             "web.it_aa7b77a3-c765-464e-a4fa-29ce6dd50346",
             "web.it_211f2187-41f2-489f-ba63-73f004f21c66"
             ]
    for guid in guids:
        fc.reg_file_in_cont(files_.first(guid=guid), container, 'input')

    # Prepare trf script
    script = task.task_type.trf_template
    # TO_DO just for test add "1" - script1.sh- only emulate, not real jobs
    pipeline_path_name = 'paleomix_bam'
    swdir='/s/ls2/users/poyda/swp/' + pipeline_path_name +'/'
    script = "/bin/bash " + swdir + "genref.sh && /bin/bash " + swdir + "runtmplgen.sh -t 1>bam.out 2>bam.err & ;"
    script += "/bin/bash " + swdir + "split.sh -t " + str(rn)
    script += script_add

    # Save rn as task param
    task.params = str(rn)
    tasks_.save(task)

    logger.debug("payload2: script " + script)
    logger.debug("payload2: send_job " + container.guid)
    send_job_(task, container, script)

    return True


def payload3(task):
    """
    run1 - N parallel jobs. {N} = sequence 0..01,0..02,...,N, not less than 2 placeholders
    #TODO deal with {N}.fastq.bz2 ??
    input: Makefile.{N}, *.fasta.{sfx list}, *1.{N}.fastq, *2.{N}.fastq
    output: likely reads{N}.tgz, maps{N}.tgz
    :param task:
    :return:
    """
    logger.debug("payload3: Start")

    #### Prepare
    # Check type of task
    task_type = task.task_type
#    if task_type.id != 3or6?:
#        raise WebpandaError("Illegal task_type.id")

    # Get user
    user = users_.get(task.owner_id)

    n=10
    if task.params is not None:
        n=int(task.params)
        if n==0:
            n=10


    task.tag = "task." + commands.getoutput('uuidgen')
    tasks_.save(task)

    # Get containers
    input_cont = conts_.get(task.input)
    #TO_DO do smth with output container?
    output_cont = conts_.get(task.output)

    for jobname in gen_sfx("",n):
        # Get container
        container = Container()
        container.guid = task.tag + "."+jobname
        conts_.save(container)

        # Add input files to container
        files_template_list = task_type.ifiles_template.split(',')
        for item in input_cont.files:
            f = item.file
            for file_template in files_template_list:
                # TO_DO: Change file template here
                m = re.match(file_template, f.lfn)
                if m is not None:
                    # Register file in container
                    fc.reg_file_in_cont(f, container, 'input')

        # reg additional output
        fc.reg_file_in_cont_byname(user, jobname+'.reads.tgz', container, 'output')
        fc.reg_file_in_cont_byname(user, jobname + '.maps.tgz', container, 'output')

        # Prepare trf script
        script = task.task_type.trf_template
        # TO_DO just for test - only emulate, not real jobs
        pipeline_path_name = 'paleomix_bam'
        swdir = '/s/ls2/users/poyda/swp/' + pipeline_path_name +'/'
        script = "/bin/bash "+swdir+"run11.sh -t " +jobname

        send_job_(task, container, script)

    return True


def gen_sfx(pre, n, end=""):
    # return list of range (1,n) with addition of prefix and end, and use equal placeholders for all numbers from sequence
    # not more than 999!!!
    #r = range(1, n)
    r=[]
    k = n
    nc = 1  # number of 0..0 prefix in list, - fon n <10: nc=1 : 01,02,..,09
    while k >= 100:
        nc += 1
        k = k // 10
    j = nc
    pp = ""
    ppf = 1
    while j > 0:
        pp += "0"
        j -= 1
    for i in xrange(n):
        if i == 9:
            pp = pp[:-1]
        elif i == 99:
            pp = pp[:-1]
        r.append(pre+pp+str(i+1)+end)
    return r


def getn(fsize):
    basen = 1610612736  # 1.5G - we has 3.6G for small biotask, and 175G for 135 subtasks for bigbiotask
    basedst = 2
    rn = 0
    n = int(fsize // basen)
    if 10 < n < 150:
        rn = n
    elif n >= 150:
        rn = 200
    elif 1 <= n <= 10:
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
    # deal with fastq.bz2 input files
    basen = 240*1024*1024  # 240Mb - bz2 ratio from x6 to x5 - we has 650M for small biotask, and 240M for 135 subtasks for ??G bigbiotask
    basedst = 2
    rn = 0
    n = int(fsize // basen)
    if 10 < n < 150:
        rn = n
    elif n >= 150:
        rn = 200
    elif 1 <= n <= 10:
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
