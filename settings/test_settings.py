import os

USE_TZ = True
TIMEZONE_ZONE = "UTC"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "surfsight",
        "USER": "julianbaumgartner",
        "PASSWORD": "",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}
INSTALLED_APPS = ("counter",)

SECRET_KEY = 'asdjf;lasdjflasdjflasdfjasldfj'
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


AGGREGATION_DATAPOINT_TIME_INTERVAL = 5
AVERAGE_DATAPOINT_TIME_INTERVAL = 30
