import json
from webpanda.async import celery
from webpanda.pipelines.scripts import main


@celery.task
def cron_paleomix_main():
    return json.dumps(main.run())


@celery.task
def cron_paleomix_main_check_running_tasks():
    return json.dumps(main.check_running_tasks())
