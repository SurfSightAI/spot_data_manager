import django

django.setup()

import pytest

from counter.enums import HourIdentifierEnum, MonthIdentifierEnum
from counter.models import (
    AggregateDataPoint,
    AverageDataPoint,
    DetectionDataPoint,
    HourlyAverageDataPoint,
    Spot,
)

from .factories import create_data


@pytest.mark.django_db
def test_data():
    create_data()
    spot = Spot.objects.first()
    assert bool(spot)

    assert len(DetectionDataPoint.objects.filter(spot=spot)) > 10

    assert AggregateDataPoint.objects.exists()

    assert isinstance(AverageDataPoint.objects.first().hour_id, HourIdentifierEnum)
    assert isinstance(AverageDataPoint.objects.first().month_id, MonthIdentifierEnum)

    assert HourlyAverageDataPoint.objects.first()
