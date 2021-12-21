import os

from dotenv import load_dotenv

USE_TZ = True
TIMEZONE_ZONE = "UTC"

load_dotenv(".env")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DATABASE_NAME"],
        "USER": os.environ["DATABASE_USER"],
        "PASSWORD": os.environ["DATABASE_PASSWORD"],
        "HOST": os.environ["DATABASE_HOST"],
        "PORT": os.environ["DATABASE_PORT"],
    }
}
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "counter",
    "rest_framework",
    "rest_framework.authtoken",
    "django_extensions",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

SECRET_KEY = os.environ["SECRET_KEY"]
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


AGGREGATION_DATAPOINT_TIME_INTERVAL = 5
AVERAGE_DATAPOINT_TIME_INTERVAL = 30
