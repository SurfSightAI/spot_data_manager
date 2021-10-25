import datetime
import logging

import pytz
from astral import LocationInfo, sun
from django.conf import settings
from django.db import models
from django.db.models import Q, Avg
from django.db.models.signals import post_save
from django.dispatch import receiver
from enumfields import EnumIntegerField
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from statistics import mean
import requests
from .enums import HourIdentifierEnum, MonthIdentifierEnum, DayIdentifierEnum


LOGGER = logging.getLogger(__name__)


class SpotManager(models.Manager):
    def active(self, cam_check=True):
        queryset = super().get_queryset()
        if cam_check:
            for spot in queryset:
                spot.check_cam()
        return (
            queryset.filter(
                Q(enabled=True) &
                Q(sunrise__lt=datetime.datetime.now(pytz.utc)) &
                Q(sunset__gt=datetime.datetime.now(pytz.utc))
            )
        )


class Spot(models.Model):
    name = models.CharField(blank=False, null=True, max_length=100)
    major_city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    lat = models.FloatField(blank=True, null=True)
    lng = models.FloatField(blank=True, null=True)
    timezone = models.CharField(blank=True, null=True, max_length=200)
    url = models.CharField(blank=True, null=True, max_length=200)
    sunrise = models.DateTimeField(blank=True, null=True)
    sunset = models.DateTimeField(blank=True, null=True)
    enabled = models.BooleanField(default=True)
    current_count = models.IntegerField(blank=True, null=True)

    objects = SpotManager()

    def __str__(self):
        return self.name

    def current_time(self):
        return datetime.datetime.now(pytz.timezone(self.timezone))
    
    def local_sunrise_time(self):
        return self.sunrise.astimezone(pytz.timezone(self.timezone)).strftime("%H:%M:%S")

    def local_sunset_time(self):
        return self.sunset.astimezone(pytz.timezone(self.timezone)).strftime("%H:%M:%S")
        
    def is_active(self):
        return self.sunrise < datetime.datetime.now(pytz.utc) < self.sunset

    def update_times(self):
        try:
            loc = LocationInfo(self.major_city, self.country, "UTC", self.lat, self.lng)
            data = sun.sun(loc.observer, datetime.datetime.now(pytz.utc))

            self.sunrise = data.get("sunrise")
            self.sunset = data.get("sunset")
            self.save()

        except Exception as e:
            LOGGER.error(f"ERROR updating sunrise and sunset: {e}")
            raise Exception(f"ERROR updating sunrise and sunset: {e}")

    def aggregate_datapoints(self):
        """
        TODO: Currently, we are just using the max count from the past time interval to create the Aggregate data point.
        We should get some weighted averages calc going on the data points for a more accurate average count.
        """
        time_interval = settings.AGGREGATION_DATAPOINT_TIME_INTERVAL
        time = datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes=int(time_interval))
        points = DetectionDataPoint.objects.values_list("count", flat=True).filter(
            spot=self, timestamp__gt=time
        )
        if bool(points):
            return AggregateDataPoint.objects.create(spot=self, count=max(points))

    def average_aggregated_datapoints(self):
        """
        TODO: Currently, we are just using the max count from the past time interval to create the Aggregate data point.
        We should get some weighted averages calc going on the data points for a more accurate average count.
        """
        time_interval = settings.AVERAGE_DATAPOINT_TIME_INTERVAL
        time = datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes=int(time_interval))
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
        
        averages = AverageDataPoint.objects.values('hour_id').annotate(count_avg=Avg("count")).filter(spot=self)
        for av in averages:
            HourlyAverageDataPoint.objects.update_or_create(spot=self, hour_id=av.get("hour_id"), defaults=dict(count=av.get("count_avg")))
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
    """ The historical average count of surfers in the watter for a spot and hour of the day."""
    spot = models.ForeignKey(Spot, on_delete=models.CASCADE)
    hour_id = EnumIntegerField(HourIdentifierEnum)
    count = models.IntegerField(default=0)



class AverageDataPoint(models.Model):
    """Averaged data point. This will average all the Aggregate from the last AVERAGE_DATAPOINT_TIME_INTERVAL"""

    spot = models.ForeignKey(Spot, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    # id info saved based on local timezone
    hour_id = EnumIntegerField(HourIdentifierEnum, null=True)
    day_id = EnumIntegerField(DayIdentifierEnum, null=True)
    month_id = EnumIntegerField(MonthIdentifierEnum, null=True)

class AggregateDataPoint(models.Model):
    """Aggregated data point. This will average all the DetectionDataPoints from the last AGGREGATION_DATAPOINT_TIME_INTERVAL"""

    spot = models.ForeignKey(Spot, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)


class DetectionDataPoint(models.Model):
    """Base level data point. Will be created ever ~30 seconds per spot"""

    spot = models.ForeignKey(Spot, on_delete=models.CASCADE, null=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(default=0)


@receiver(post_save, sender=AverageDataPoint, dispatch_uid="create_average_datapoint")
def create_average_datapoint_hour_id(sender, instance, created, **kwargs):
    """When a new AverageDataPoint is created, add its hour_id"""
    if created:
        local_time = instance.timestamp.astimezone(pytz.timezone(instance.spot.timezone))
        instance.hour_id = HourIdentifierEnum(instance.timestamp.hour)
        instance.day_id = DayIdentifierEnum(instance.timestamp.weekday())
        instance.month_id = MonthIdentifierEnum(instance.timestamp.month)
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
