from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

HOURS_LIMIT = 96
DISPLAY_LIMIT = 200

SQLALCHEMY_TRACK_MODIFICATIONS = False

SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url='mysql+mysqldb://it:ivanpass@localhost:3306/pandaweb_test')
    }
SCHEDULER_EXECUTORS = {
    'default': {'type': 'threadpool', 'max_workers': 20}
}
SCHEDULER_JOB_DEFAULTS = {
    'coalesce': False,
    'max_instances': 3
}
SCHEDULER_VIEWS_ENABLED = True