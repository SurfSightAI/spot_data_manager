import os

USE_TZ = True
TIMEZONE_ZONE = "UTC"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ["DATABASE_NAME"],
        "USER": os.environ["DATABASE_USER"],
        "PASSWORD": os.environ["DATABASE_PASSWORD"],
        "HOST": os.environ["DATABASE_HOST"],
        "PORT": os.environ["DATABASE_PORT"],
    }
}

INSTALLED_APPS = ("counter",)

SECRET_KEY = os.environ["SECRET_KEY"]
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


AGGREGATION_DATAPOINT_TIME_INTERVAL = 5
AVERAGE_DATAPOINT_TIME_INTERVAL = 30
