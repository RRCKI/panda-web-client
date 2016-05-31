from webpanda.core import db


class TransferTask(db.Model):
    __tablename__ = 'transfertasks'
    id = db.Column(db.Integer, primary_key=True)
    replica_id = db.Column(db.Integer, db.ForeignKey('replicas.id'))
    se = db.Column(db.String(40))
    task_id = db.Column(db.String(40))
    task_status = db.Column(db.String(20))


class TaskMeta(db.Model):
    __tablename__ = 'celery_taskmeta'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(255))
    status = db.Column(db.String(50))
    result = db.Column(db.BLOB)
    date_done = db.Column(db.DateTime)
    traceback = db.Column(db.Text)


class TaskSetMeta(db.Model):
    __tablename__ = 'celery_tasksetmeta'
    id = db.Column(db.Integer, primary_key=True)
    taskset_id = db.Column(db.String(255))
    result = db.Column(db.BLOB)
    date_done = db.Column(db.DateTime)