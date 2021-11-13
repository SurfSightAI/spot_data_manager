import random

import pytest

from counter.models import DetectionDataPoint, Spot

spot_params = {
    "name": "Lowers",
    "major_city": "San Clemente",
    "country": "United States",
    "postal_code": 92672,
    "url": "https://cams.cdn-surfline.com/cdn-wc/wc-lowers/playlist.m3u8",
}


@pytest.mark.django_db
def create_spot():
    spot = Spot.objects.create(**spot_params)
    spot.update_times()
    return spot


@pytest.mark.django_db
def create_data():
    spot = Spot.objects.first()
    if not spot:
        spot = create_spot()

    # Create some random data
    for i in range(30):
        DetectionDataPoint.objects.create(spot=spot, count=random.randint(3, 40))

    # Let the rest of the data get created via and model methods
    spot.aggregate_datapoints()
    spot.average_aggregated_datapoints()
    spot.update_hourly_averages()
