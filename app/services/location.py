from functools import lru_cache
from math import atan2, cos, radians, sin, sqrt


TELANGANA_CITIES = [
    {"name": "Hyderabad", "lat": 17.385, "lng": 78.4867},
    {"name": "Warangal", "lat": 17.9689, "lng": 79.5941},
    {"name": "Karimnagar", "lat": 18.4386, "lng": 79.1288},
    {"name": "Nizamabad", "lat": 18.6725, "lng": 78.0941},
    {"name": "Khammam", "lat": 17.2473, "lng": 80.1514},
]


@lru_cache(maxsize=4096)
def calculate_distance(lat1, lon1, lat2, lon2):
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius * c


def fallback_city_coordinates(city_name="Hyderabad"):
    normalized = (city_name or "").strip().lower()
    for city in TELANGANA_CITIES:
        if city["name"].lower() == normalized:
            return city
    return TELANGANA_CITIES[0]
