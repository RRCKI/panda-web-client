# -*- coding: utf-8 -*-
"""
    webpanda.tasks.models
    ~~~~~~~~~~~~~~~~~~~~~~
    Task models
"""

from webpanda.core import db, WebpandaError
from webpanda.helpers import JsonSerializer


tasks_jobs = db.Table(
    'tasks_jobs',
    db.Column('task_id', db.Integer(), db.ForeignKey('tasks.id')),
    db.Column('job_id', db.Integer(), db.ForeignKey('jobs.id')))


class TaskTypeJsonSerializer(JsonSerializer):
    pass


class TaskType(TaskTypeJsonSerializer, db.Model):
    __tablename__ = 'task_types'
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(256))
    trf_template = db.Column(db.String(1024))
    ifiles_template = db.Column(db.String(1024))
    ofiles_template = db.Column(db.String(1024))
    tasks = db.relationship("Task", back_populates="task_type")

    def __repr__(self):
        return '<TaskType id=%s>' % self.id


class PipelineTypeJsonSerializer(JsonSerializer):
    __json_public__ = ['id', 'name']


class PipelineType(PipelineTypeJsonSerializer, db.Model):
    __tablename__ = 'pipeline_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    init_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    pre_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    split_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    prun_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    merge_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    post_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    finish_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    pipelines = db.relationship("Pipeline", back_populates="pipeline_type")

    def __repr__(self):
        return '<PipelineType id=%s>' % self.id

    def get_next_task_type_id(self, current_state):
        """
        Returns Type ID of next task or None if pipeline finished
        :return: int or None
        """
        # Set list of all states
        states = ['init_task', "pre_task", "split_task", "prun_task", "merge_task", "post_task", "finish_task"]

        # Check input param
        if current_state not in states:
            raise WebpandaError("Illegal current_state param")

        # Remove all state before current state (including)
        for state in states:
            states.remove(state)
            if state == current_state:
                break

        # Find next not None state
        for state in states:
            if getattr(self, state + 'type_id') is not None:
                return getattr(self, state + 'type_id')

        return None


class TaskJsonSerializer(JsonSerializer):
    pass


class Task(TaskJsonSerializer, db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_type_id = db.Column(db.Integer, db.ForeignKey('task_types.id'))
    task_type = db.relationship("TaskType", back_populates="tasks")
    tag = db.Column(db.String(256))
    creation_time = db.Column(db.DateTime)
    modification_time = db.Column(db.DateTime)
    status = db.Column(db.String(64), default='defined')
    jobs = db.relationship('Job', secondary=tasks_jobs)
    trf = db.Column(db.String(1024))
    input = db.Column(db.Integer, db.ForeignKey('containers.id'), default=None)
    output = db.Column(db.Integer, db.ForeignKey('containers.id'), default=None)
    comment = db.Column(db.String(1024))

    def __repr__(self):
        return '<Task id=%s tag=%s>' % (self.id, self.tag)


class PipelineJsonSerializer(JsonSerializer):
    __json_public__ = ['id', 'name']


class Pipeline(PipelineJsonSerializer, db.Model):
    __tablename__ = 'pipelines'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('pipeline_types.id'))
    pipeline_type = db.relationship("PipelineType", back_populates="pipelines")
    name = db.Column(db.String(256))
    tag = db.Column(db.String(256))
    current_state = db.Column(db.String(256))
    status = db.Column(db.String(256))

    init_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    pre_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    split_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    prun_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    merge_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    post_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    finish_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)

    def __repr__(self):
        return '<Pipeline id=%s name=%s>' % (self.id, self.name)

    def get_current_task_id(self):
        """
        Returns current task id
        :return: int
        """
        try:
            current_task_id = getattr(self, self.current_state + "_id")
        except:
            raise WebpandaError("Unable to get current task ID")
        return current_task_id









