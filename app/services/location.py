from .recommendations import haversine_distance


TELANGANA_CITIES = [
    {"name": "Hyderabad", "lat": 17.385, "lng": 78.4867},
    {"name": "Warangal", "lat": 17.9689, "lng": 79.5941},
    {"name": "Karimnagar", "lat": 18.4386, "lng": 79.1288},
    {"name": "Nizamabad", "lat": 18.6725, "lng": 78.0941},
    {"name": "Khammam", "lat": 17.2473, "lng": 80.1514},
]


def normalize_telangana_city(city_name):
    if not city_name:
        return None
    cleaned = city_name.strip().lower()
    for city in TELANGANA_CITIES:
        if city["name"].lower() == cleaned:
            return city["name"]
    for city in TELANGANA_CITIES:
        if cleaned in city["name"].lower() or city["name"].lower() in cleaned:
            return city["name"]
    return None


def resolve_telangana_city(lat, lng):
    nearest = min(
        TELANGANA_CITIES,
        key=lambda city: haversine_distance(lat, lng, city["lat"], city["lng"]),
    )
    distance = haversine_distance(lat, lng, nearest["lat"], nearest["lng"])
    return {
        "city": nearest["name"],
        "city_lat": nearest["lat"],
        "city_lng": nearest["lng"],
        "distance_to_city_center": round(distance, 1),
    }
