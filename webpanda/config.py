from datetime import timedelta

HOURS_LIMIT = 96
DISPLAY_LIMIT = 200

SQLALCHEMY_TRACK_MODIFICATIONS = False


# Cron jobs
CELERYBEAT_SCHEDULE = {
    'paleomix_main_cron': {
        'task': 'webpanda.async.pipelines.cron_paleomix_main',
        'schedule': timedelta(seconds=60),
        #'schedule': crontab()
    },
    'paleomix_main_cron3': {
        'task': 'webpanda.async.pipelines.cron_paleomix_main_check_running_tasks',
        'schedule': timedelta(seconds=60),
        #'schedule': crontab()
    },
    'main_cron_add': {
        'task': 'webpanda.async.scripts.cron_add',
        'schedule': timedelta(seconds=60),
        #'schedule': crontab()
    }
}
