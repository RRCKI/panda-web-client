from datetime import timedelta

HOURS_LIMIT = 96
DISPLAY_LIMIT = 200

SQLALCHEMY_TRACK_MODIFICATIONS = False


# Cron jobs
CELERYBEAT_SCHEDULE = {
    # Executes every Monday morning at 7:30 A.M
    'paleomix_main_cron': {
        'task': 'webpanda.async.scripts.cron_paleomix_test',
        'schedule': timedelta(seconds=5),
        #'schedule': crontab()
    },
}
