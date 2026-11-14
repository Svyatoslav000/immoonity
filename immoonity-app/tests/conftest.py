import pytest

from app import create_app
from immoonity_core.engine import load_models


@pytest.fixture(scope="session")
def models():
    return load_models()


@pytest.fixture()
def client():
    return create_app().test_client()


EARTH_OK = {"sex": "M", "vo2max": "48", "pullups": "15", "pushups": "60"}
FLIGHT_OK = {"il6_b": "2", "il6_a": "2.2", "nlr_b": "1.8", "nlr_a": "2.0", "ebv": "40", "cortb": "400",
             "corta": "420", "days": "180"}
