import json
from webpanda.async import celery
from webpanda.pipelines.scripts import paleomix_main


@celery.task
def cron_paleomix_main():
    return json.dumps(paleomix_main.run())


@celery.task
def cron_paleomix_main_check_running_tasks():
    return json.dumps(paleomix_main.check_running_tasks())
