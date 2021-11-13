import django

django.setup()

import pytest
import requests

from counter.models import Spot

from .factories import create_spot, spot_params


@pytest.mark.django_db
def test_spot():

    spot = create_spot()

    # Spot returns form db
    assert bool(Spot.objects.last())

    # General spot info
    assert spot.name == spot_params.get("name")
    assert spot.major_city == spot_params.get("major_city")
    assert spot.country == spot_params.get("country")
    assert spot.postal_code == spot_params.get("postal_code")

    # Spot locational data
    assert bool(spot.lat)
    assert bool(spot.lng)
    assert bool(spot.timezone)

    # Spot url works
    r = requests.get(spot.url)
    assert r.ok

    # Update spot sunrise and sunset times
    assert bool(spot.sunrise)
    assert bool(spot.sunset)
