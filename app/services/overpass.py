import time
from typing import Dict, List, Optional, Tuple

import requests

from .location import calculate_distance


OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"
DEFAULT_RADIUS_METERS = 6000
CACHE_TTL_SECONDS = 300
_OVERPASS_CACHE: Dict[Tuple[float, float, int, str, str], Tuple[float, List[dict]]] = {}


def _cache_key(lat: float, lon: float, radius_m: int, amenity: str, keyword: str):
    return (round(lat, 3), round(lon, 3), radius_m, amenity or "", keyword.strip().lower())


def _extract_place(element):
    tags = element.get("tags", {})
    lat = element.get("lat", element.get("center", {}).get("lat"))
    lon = element.get("lon", element.get("center", {}).get("lon"))
    if lat is None or lon is None:
        return None

    amenity = tags.get("amenity", "restaurant")
    name = tags.get("name") or tags.get("brand") or f"Unnamed {amenity.replace('_', ' ').title()}"
    address_bits = [
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
    ]

    return {
        "id": f"osm-{element.get('type', 'node')}-{element['id']}",
        "name": name,
        "lat": lat,
        "lon": lon,
        "lng": lon,
        "type": amenity,
        "cuisine": tags.get("cuisine", "").replace(";", ", "),
        "address": ", ".join(bit for bit in address_bits if bit),
        "rating": None,
        "delivery_time": None,
        "image_url": None,
        "source": "osm",
        "url": None,
    }


def fetch_overpass_restaurants(
    lat: float,
    lon: float,
    radius_m: int = DEFAULT_RADIUS_METERS,
    amenity: str = "",
    keyword: str = "",
):
    cache_key = _cache_key(lat, lon, radius_m, amenity, keyword)
    cached = _OVERPASS_CACHE.get(cache_key)
    if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    amenity_pattern = amenity if amenity else "restaurant|cafe|fast_food|food_court"
    query = f"""
    [out:json][timeout:15];
    (
      node["amenity"~"{amenity_pattern}"](around:{radius_m},{lat},{lon});
      way["amenity"~"{amenity_pattern}"](around:{radius_m},{lat},{lon});
      relation["amenity"~"{amenity_pattern}"](around:{radius_m},{lat},{lon});
    );
    out center tags;
    """

    response = requests.get(OVERPASS_ENDPOINT, params={"data": query}, timeout=20)
    response.raise_for_status()

    seen = set()
    places: List[dict] = []
    normalized_keyword = keyword.strip().lower()

    for element in response.json().get("elements", []):
        place = _extract_place(element)
        if not place:
            continue

        haystack = " ".join(
            [
                place["name"],
                place["type"],
                place["cuisine"],
                place["address"],
            ]
        ).lower()
        if normalized_keyword and normalized_keyword not in haystack:
            continue

        dedupe_key = (place["name"].lower(), round(place["lat"], 4), round(place["lon"], 4))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        place["distance_km"] = round(calculate_distance(lat, lon, place["lat"], place["lon"]), 2)
        places.append(place)

    places.sort(key=lambda item: item["distance_km"])
    _OVERPASS_CACHE[cache_key] = (time.time(), places)
    return places


def safe_fetch_overpass_restaurants(
    lat: float,
    lon: float,
    radius_m: int = DEFAULT_RADIUS_METERS,
    amenity: str = "",
    keyword: str = "",
):
    try:
        return fetch_overpass_restaurants(lat, lon, radius_m=radius_m, amenity=amenity, keyword=keyword), None
    except requests.RequestException as exc:
        return [], str(exc)
