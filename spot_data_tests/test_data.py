import django

django.setup()

import pytest

from counter.enums import HourIdentifierEnum, MonthIdentifierEnum, SurfQualityRating
from counter.models import (
    SurfQualityDataPoint,
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


    assert SurfQualityDataPoint.objects.first()
    assert isinstance(SurfQualityDataPoint.objects.first().rating, SurfQualityRating)
    assert isinstance(SurfQualityDataPoint.objects.first().hour_id, HourIdentifierEnum)
