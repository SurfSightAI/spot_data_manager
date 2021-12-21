import datetime
import logging
from statistics import mean

import pytz
import requests
from astral import LocationInfo, sun
from django.conf import settings
from django.db import models
from django.db.models import Avg, F, Func, Q
from django.db.models.fields import DateTimeField
from django.db.models.signals import post_save
from django.dispatch import receiver
from enumfields import EnumIntegerField, EnumField
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count

from .enums import DayIdentifierEnum, HourIdentifierEnum, MonthIdentifierEnum, SurfQualityRating

LOGGER = logging.getLogger(__name__)


class ConvertToTimezone(Func):
    """
    Construct sql clause to annotate localized times of each spot onto the queryset.
    Times are stored as UTC in the database, comparing them to calculate whether a spot
    is active yield inaccurate resuts. So we need the localized sunrise, current time, and sunset times.
    """

    output_field = DateTimeField()

    def __init__(self, timezone_field, datetime_field=None, now=False, **extra):
        if now:
            expressions = datetime.datetime.now().astimezone(pytz.utc), timezone_field
        else:
            expressions = datetime_field, timezone_field

        super(ConvertToTimezone, self).__init__(*expressions, **extra)

    def as_sql(
        self,
        compiler,
        connection,
        fn=None,
        template=None,
        arg_joiner=None,
        **extra_context,
    ):
        params = []
        sql_parts = []
        for arg in self.source_expressions:
            arg_sql, arg_params = compiler.compile(arg)
            sql_parts.append(arg_sql)
            params.extend(arg_params)

        return "%s AT TIME ZONE %s" % tuple(sql_parts), params


class SpotManager(models.Manager):
    def active(self, cam_check=True):
        """
        Return spots where the sun up and the cam is operational
        Args:
            cam_check (bool, optional):
                Defaults to True.
                Checking cams in succession can take a while, thread the tasks to speed things upk.

        Returns:
            Queryset[Spot]: All active spots
        """

        queryset = super().get_queryset()
        if cam_check:
            pool = ThreadPool(cpu_count())
            pool.map(check_cam, queryset)
            pool.close()
            pool.join()

        return queryset.annotate(
            local_sunrise=ConvertToTimezone("timezone", datetime_field="_sunrise"),
            local_sunset=ConvertToTimezone("timezone", datetime_field="_sunset"),
            local_now=ConvertToTimezone("timezone", now=True),
        ).filter(
            Q(enabled=True)
            & Q(local_sunrise__lt=F("local_now"))
            & Q(local_sunset__gt=F("local_now"))
        )


class Spot(models.Model):
    """A surfline surf spot with cam"""
    class Meta:
        app_label="counter"
        
    name = models.CharField(blank=False, null=True, max_length=100)
    major_city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    lat = models.FloatField(blank=True, null=True)
    lng = models.FloatField(blank=True, null=True)
    timezone = models.CharField(blank=True, null=True, max_length=200)
    
    current_surf_quality = EnumField(SurfQualityRating, blank=True, max_length=12)

    # Cam Url
    url = models.CharField(blank=True, null=True, max_length=200)

    # Private sunset/sunrise are utc aware datetime objects
    _sunrise = models.DateTimeField(blank=True, null=True)
    _sunset = models.DateTimeField(blank=True, null=True)

    # Public sunrise/sunset are local times based on spot timezone
    sunrise = models.TimeField(blank=True, null=True, db_index=True)
    sunset = models.TimeField(blank=True, null=True, db_index=True)

    enabled = models.BooleanField(default=True, db_index=True)
    current_count = models.IntegerField(blank=True, null=True)

    objects = SpotManager()

    def __str__(self):
        return self.name

    def current_time(self):
        return datetime.datetime.now(pytz.timezone(self.timezone))

    def local_sunrise_time(self):
        return self.sunrise

    def local_sunset_time(self):
        return self.sunset

    def is_active(self):
        return self.sunrise < datetime.datetime.now(pytz.utc).time() < self.sunset

    def update_times(self):
        try:
            loc = LocationInfo(self.major_city, self.country, "UTC", self.lat, self.lng)
            data = sun.sun(loc.observer, datetime.datetime.now(pytz.utc))

            self._sunrise = data.get("sunrise")
            self._sunset = data.get("sunset")
            self.sunrise = self._sunrise.astimezone(pytz.timezone(self.timezone)).time()
            self.sunset = self._sunset.astimezone(pytz.timezone(self.timezone)).time()
            self.save()

        except Exception as e:
            LOGGER.error(f"ERROR updating sunrise and sunset: {e}")
            raise Exception(f"ERROR updating sunrise and sunset: {e}")

    def aggregate_datapoints(self):
        """TODO: Weighted average?
        Aggregate the DetectionDataPoints from the last AGGREGATION_DATAPOINT_TIME_INTERVAL

        Returns:
            AggregateDataPoint: The DetectionDataPoint max count from the last AGGREGATION_DATAPOINT_TIME_INTERVAL
        """
        time_interval = settings.AGGREGATION_DATAPOINT_TIME_INTERVAL
        time = datetime.datetime.now(pytz.utc) - datetime.timedelta(
            minutes=int(time_interval)
        )
        points = DetectionDataPoint.objects.values_list("count", flat=True).filter(
            spot=self, timestamp__gt=time
        )
        if bool(points):
            return AggregateDataPoint.objects.create(spot=self, count=max(points))

    def average_aggregated_datapoints(self):
        """TODO: Weighted average?
        Average the AggregateDataPoints from the last AVERAGE_DATAPOINT_TIME_INTERVAL

        Returns:
            AverageDataPoint: The AggregateDataPoint count mean from the last AVERAGE_DATAPOINT_TIME_INTERVAL
        """
        time_interval = settings.AVERAGE_DATAPOINT_TIME_INTERVAL
        time = datetime.datetime.now(pytz.utc) - datetime.timedelta(
            minutes=int(time_interval)
        )
        points = AggregateDataPoint.objects.values_list("count", flat=True).filter(
            spot=self, timestamp__gt=time
        )
        if bool(points):
            return AverageDataPoint.objects.create(spot=self, count=int(mean(points)))

    def update_hourly_averages(self):
        """
        Recalculate the HourlyAverageDataPoints.
        NOTE this is a thirsty method given that it will be aggregating all the AverageDataPoint in the db
        """

        averages = (
            AverageDataPoint.objects.values("hour_id")
            .annotate(count_avg=Avg("count"))
            .filter(spot=self)
        )
        for av in averages:
            HourlyAverageDataPoint.objects.update_or_create(
                spot=self,
                hour_id=av.get("hour_id"),
                defaults=dict(count=av.get("count_avg")),
            )
        return averages

    def check_cam(self):
        """Ping the cam url, disable the spot if the cam is down"""
        r = requests.get(self.url)
        if r.ok:
            self.enabled = True
        else:
            self.enabled = False
        self.save()


class HourlyAverageDataPoint(models.Model):
    """The historical average count of surfers in the watter for a spot and hour of the day."""
    class Meta:
        app_label="counter"

    spot = models.ForeignKey(Spot, on_delete=models.CASCADE)
    hour_id = EnumIntegerField(HourIdentifierEnum)
    count = models.IntegerField(default=0)


class AverageDataPoint(models.Model):
    """Averaged data point. This will average all the Aggregate from the last AVERAGE_DATAPOINT_TIME_INTERVAL"""
    class Meta:
        app_label="counter"

    spot = models.ForeignKey(Spot, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    # id info saved based on local timezone
    hour_id = EnumIntegerField(HourIdentifierEnum, null=True)
    day_id = EnumIntegerField(DayIdentifierEnum, null=True)
    month_id = EnumIntegerField(MonthIdentifierEnum, null=True)


class AggregateDataPoint(models.Model):
    """Aggregated data point. This will average all the DetectionDataPoints from the last AGGREGATION_DATAPOINT_TIME_INTERVAL"""
    class Meta:
        app_label="counter"

    spot = models.ForeignKey(Spot, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)


class DetectionDataPoint(models.Model):
    """Base level data point. Will be created ever ~30 seconds per spot"""
    class Meta:
        app_label="counter"

    spot = models.ForeignKey(Spot, on_delete=models.CASCADE, null=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(default=0)


@receiver(post_save, sender=AverageDataPoint, dispatch_uid="create_average_datapoint")
def create_average_datapoint_hour_id(sender, instance, created, **kwargs):
    """When a new AverageDataPoint is created, add its hour_id, day_id, and month_id based on the timestamp"""
    if created:
        local_time = instance.timestamp.astimezone(
            pytz.timezone(instance.spot.timezone)
        )
        instance.hour_id = HourIdentifierEnum(local_time.hour)
        instance.day_id = DayIdentifierEnum(local_time.weekday())
        instance.month_id = MonthIdentifierEnum(local_time.month)
        instance.save()


@receiver(post_save, sender=Spot, dispatch_uid="create_spot_data")
def create_spot_data(sender, instance, created, **kwargs):
    """When new Spot is created, calculate and save the locational info."""
    if created:
        tz_find = TimezoneFinder()
        geolocator = Nominatim(user_agent="SurfSight")

        location = geolocator.geocode(
            {
                "city": instance.major_city,
                "country": instance.country,
                "postal_code": instance.postal_code,
            }
        )

        instance.lat = location.latitude
        instance.lng = location.longitude
        tz_find = TimezoneFinder()
        tz = tz_find.timezone_at(lng=instance.lng, lat=instance.lat)
        instance.timezone = tz
        instance.save()


def check_cam(spot):
    r = requests.get(spot.url)
    spot.enabled = r.ok
    spot.save()
