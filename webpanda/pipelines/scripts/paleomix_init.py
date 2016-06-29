# -*- coding: utf-8 -*-
from datetime import datetime
import re
from webpanda.core import WebpandaError
from webpanda.services import tasks_, conts_


def run(task):
    try:
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
    Checks if neccessary files in input container
    :param task:
    :return:
    """
    # Check type of task
    task_type = task.task_type
    if task_type.id != 2:
        raise WebpandaError("Illegal task_type.id")

    # Get containers
    input_cont = conts_.get(task.input)
    output_cont = conts_.get(task.output)

    # Get list of files to search for
    files_template_list = task_type.ifiles_template.split(',')

    for item in input_cont.files:
        f = item.file

        for file_template in files_template_list:
            m = re.match(file_template. f.lfn)
            if m is not None:
                files_template_list.remove(file_template)

    if len(files_template_list) > 0:
        raise WebpandaError("Input files not found in input container")

    return True
