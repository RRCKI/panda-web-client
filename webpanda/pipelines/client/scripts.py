from datetime import datetime
from webpanda.services import tasks_, pipelines_, pipeline_catalog_, task_types_
from webpanda.tasks import Pipeline, Task, PipelineType, PipelineCatalog, TaskType


def get_current_task(p):
    """
    Returns current task object
    :param p: Pipeline obj
    :return: Task obj
    """
    if not isinstance(p, Pipeline):
        raise Exception("Illegal pipeline class: not Pipeline")
    current_task_id = p.current_task_id

    current_task = tasks_.get(current_task_id)
    if not isinstance(current_task, Task):
        raise Exception("Unable to fetch current_task by id")

    return current_task


def set_current_task(p, t):
    """
    Sets current task object
    :param p: Pipeline obj
    :param t: Task obj
    :return: Pipeline obj
    """
    if not isinstance(p, Pipeline):
        raise Exception("Illegal pipeline class: not Pipeline")
    if not isinstance(t, Task):
        raise Exception("Illegal task class: not Task")

    p.current_task_id = t.id
    pipelines_.save(p)

    return p


def get_next_task(p):
    """
    Returns next task object
    :param p: Pipeline obj
    :return: Task obj
    """
    if not isinstance(p, Pipeline):
        raise Exception("Illegal pipeline class: not Pipeline")

    # Fetch current_task
    current_task_id = p.current_task_id
    current_task = tasks_.get(current_task_id)
    if not isinstance(current_task, Task):
        raise Exception("Unable to fetch current_task by id")
    current_task_type = current_task.task_type

    # Fetch pipeline_type
    pipeline_type = p.pipeline_type
    if not isinstance(pipeline_type, PipelineType):
        raise Exception("Illegal pipeline_type class: not PipelineType")

    # Fetch pipeline_catalog item
    pp_c = pipeline_catalog_.first(pipeline_type_id=pipeline_type.id, current_task_type_id=current_task_type.id)
    if not isinstance(pp_c, PipelineCatalog):
        raise Exception("Unable to fetch PipelineCatalog item")

    # Return next_task
    next_task = new_task(pp_c.next_task_type)
    next_task.owner_id = p.owner_id
    next_task.input = current_task.input
    next_task.output = current_task.output
    tasks_.save(next_task)

    # Update Pipeline obj
    set_current_task(p, next_task)
    return next_task


def get_start_task(p):
    """
    Returns start task object
    :param p: Pipeline obj
    :return: Task obj
    """
    if not isinstance(p, Pipeline):
        raise Exception("Illegal pipeline class: not Pipeline")

    # Create start_task
    start_task_type = task_types_.first(method='start')
    start_task = new_task(start_task_type.id)
    tasks_.save(start_task)

    # Update Pipeline obj
    set_current_task(p, start_task)
    return start_task


def new_task(tt):
    """
    Creates default Task obj
    :param tt: TaskType obj
    :return: Task obj
    """
    if not isinstance(tt, TaskType):
        raise Exception("Illegal tt class: not TaskType")

    t = Task()
    t.creation_time = datetime.utcnow()
    t.modification_time = datetime.utcnow()
    t.status = 'defined'
    t.task_type = tt
    return t


def is_start_task(t):
    """
    Checks if task is init
    :param t: Task obj
    :return: True/False
    """
    if not isinstance(t, Task):
        raise Exception("Illegal task class: not Task")

    return t.task_type.method == 'start'


def is_finish_task(t):
    """
    Checks if task is init
    :param t: Task obj
    :return: True/False
    """
    if not isinstance(t, Task):
        raise Exception("Illegal task class: not Task")

    return t.task_type.method == 'finish'