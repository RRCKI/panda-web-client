# -*- coding: utf-8 -*-
from datetime import datetime
from webpanda.core import WebpandaError
from webpanda.services import tasks_, conts_


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
    Split input *.1.fastq and *.2.fastq into N pieces
    Register results into output_cont
    :param task:
    :return:
    """
    N = 100

    # Get containers
    input_cont = conts_.get(task.input)
    output_cont = conts_.get(task.output)

    for item in input_cont.files:
        f = item.file

        # Find *.1.fastq file
        if ".1.fastq" in f.lfn:
            # Split file
            pass

        # Find *.2.fastq file
        if ".2.fastq" in f.lfn:
            # Split file
            pass

    return True