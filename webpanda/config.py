import os
from datetime import timedelta


class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY',
                                '51f52814-0071-11e6-a247-000ec6c2372c')
    REQUEST_STATS_WINDOW = 15

    HOURS_LIMIT = 96
    DISPLAY_LIMIT = 200

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CELERYBEAT_SCHEDULE = {
        'paleomix_main_cron': {
            'task': 'webpanda.async.pipelines.cron_paleomix_main',
            'schedule': timedelta(seconds=60),
            # 'schedule': crontab()
        },
        'paleomix_main_cron3': {
            'task': 'webpanda.async.pipelines.cron_paleomix_main_check_running_tasks',
            'schedule': timedelta(seconds=60),
            # 'schedule': crontab()
        },
        'main_cron_add': {
            'task': 'webpanda.async.scripts.cron_add',
            'schedule': timedelta(seconds=60),
            # 'schedule': crontab()
        }
    }

    LDAP_PROVIDER_URL = os.environ.get("LDAP_PROVIDER_URL", None)
    LDAP_BASE_DN = os.environ.get("LDAP_BASE_DN", None)

    AUTH_AUTH_ENDPOINT = os.environ.get("AUTH_AUTH_ENDPOINT")
    AUTH_TOKEN_ENDPOINT = os.environ.get("AUTH_TOKEN_ENDPOINT")
    AUTH_USERINFO_ENDPOINT = os.environ.get("AUTH_USERINFO_ENDPOINT")
    AUTH_REDIRECT_URI = os.environ.get("AUTH_REDIRECT_URI")
    AUTH_CLIENT = os.environ.get("AUTH_CLIENT")
    AUTH_SECRET = os.environ.get("AUTH_SECRET")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    pass


class TestingConfig(Config):
    TESTING = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
