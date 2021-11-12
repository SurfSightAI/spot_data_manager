from airflow.models import Variable

USE_TZ = True
TIMEZONE_ZONE = "UTC"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": Variable.get("DATABASE_NAME"),
        "USER": Variable.get("DATABASE_USER"),
        "PASSWORD": Variable.get("DATABASE_PASSWORD"),
        "HOST": Variable.get("DATABASE_HOST"),
        "PORT": Variable.get("DATABASE_PORT"),
    }
}
INSTALLED_APPS = ("counter",)


SECRET_KEY = Variable.get("SECRET_KEY")

AGGREGATION_DATAPOINT_TIME_INTERVAL = 5
AVERAGE_DATAPOINT_TIME_INTERVAL = 30
