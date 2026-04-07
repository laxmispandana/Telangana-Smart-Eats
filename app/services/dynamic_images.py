import json
import re
from pathlib import Path

import requests
from flask import current_app

from .image_utils import themed_restaurant_image


CACHE_FILE = Path(__file__).resolve().parents[1] / "image_cache.json"
SPOONACULAR_SEARCH_URL = "https://api.spoonacular.com/recipes/complexSearch"

FOOD_QUERY_HINTS = {
    "chicken dum biryani": [
        "Chicken Biryani authentic indian food high quality",
        "Chicken Biryani restaurant style plating",
    ],
    "mutton haleem bowl": [
        "Mutton Haleem authentic indian food high quality",
        "Haleem indian dish real photo",
    ],
    "tandoori chicken": [
        "Tandoori Chicken authentic indian food high quality",
        "Tandoori Chicken restaurant style plating",
    ],
    "talawa gosht": [
        "Talawa Gosht authentic indian food high quality",
        "Mutton fry authentic indian food high quality",
    ],
    "garlic butter naan": [
        "Garlic Butter Naan authentic indian food high quality",
        "Garlic Naan restaurant style plating",
    ],
    "paneer tikka": [
        "Paneer Tikka authentic indian food high quality",
        "Paneer Tikka restaurant style plating",
    ],
    "green salad platter": [
        "Veg Salad authentic indian food high quality",
        "Veg Salad restaurant style plating",
    ],
    "millet khichdi": [
        "Millet Khichdi authentic indian food high quality",
        "Millet Khichdi restaurant style plating",
    ],
    "egg fried rice": [
        "Egg Fried Rice authentic indian food high quality",
        "Egg Fried Rice restaurant style plating",
    ],
    "double ka meetha": [
        "Double Ka Meetha authentic indian food high quality",
        "Double Ka Meetha restaurant style plating",
    ],
    "foxtail millet bowl": [
        "Foxtail Millet Bowl authentic indian food high quality",
        "Foxtail Millet Bowl restaurant style plating",
    ],
    "protein idli plate": [
        "Protein Idli Plate indian breakfast healthy",
        "Idli Sambar south indian dish real photo",
    ],
    "grilled fish with greens": [
        "Grilled Fish healthy meal restaurant style",
        "Grilled Fish authentic indian food high quality",
    ],
    "low-oil chicken curry": [
        "Chicken Curry authentic indian food high quality",
        "Chicken Curry restaurant style plating",
    ],
    "ragi dosa": [
        "Ragi Dosa south indian dish real photo",
        "Ragi Dosa restaurant style plating",
    ],
    "yogurt fruit cup": [
        "Yogurt Fruit Bowl healthy meal restaurant style",
        "Fruit Yogurt healthy meal restaurant style",
    ],
    "peanut chutney wrap": [
        "Peanut Chutney Wrap authentic indian food high quality",
        "Veg Wrap restaurant style plating",
    ],
    "power upma": [
        "Upma south indian dish real photo",
        "Upma restaurant style plating",
    ],
    "paneer protein bowl": [
        "Paneer Bowl authentic indian food high quality",
        "Paneer Bowl restaurant style plating",
    ],
    "cold-pressed juice": [
        "Cold Pressed Juice restaurant style plating",
        "Cold Pressed Juice healthy drink high quality",
    ],
    "peri peri chicken roll": [
        "Chicken Roll restaurant style plating",
        "Peri Peri Chicken Roll authentic indian food high quality",
    ],
    "bbq chicken wings": [
        "BBQ Chicken Wings restaurant style plating",
        "Chicken Wings high quality food photo",
    ],
    "paneer shawarma": [
        "Paneer Shawarma restaurant style plating",
        "Paneer Wrap authentic indian food high quality",
    ],
    "veg loaded pizza": [
        "Veg Pizza restaurant style plating",
        "Vegetable Pizza high quality food photo",
    ],
    "chicken loaded pizza": [
        "Chicken Pizza restaurant style plating",
        "Chicken Pizza high quality food photo",
    ],
    "garlic bread": [
        "Garlic Bread restaurant style plating",
        "Garlic Bread high quality food photo",
    ],
    "caesar salad": [
        "Caesar Salad restaurant style plating",
        "Caesar Salad healthy meal high quality",
    ],
    "grilled chicken steak": [
        "Grilled Chicken healthy meal restaurant style",
        "Grilled Chicken Steak high quality food photo",
    ],
    "brown rice bowl": [
        "Brown Rice Bowl healthy meal restaurant style",
        "Brown Rice Bowl high quality food photo",
    ],
    "choco mousse": [
        "Chocolate Mousse restaurant style plating",
        "Chocolate Mousse dessert high quality",
    ],
    "veg thali": [
        "Veg Thali authentic indian food high quality",
        "Veg Thali restaurant style plating",
    ],
    "palak paneer": [
        "Palak Paneer authentic indian food high quality",
        "Palak Paneer restaurant style plating",
    ],
    "mixed veg curry": [
        "Mixed Veg Curry authentic indian food high quality",
        "Mixed Veg Curry restaurant style plating",
    ],
    "quinoa pulao": [
        "Quinoa Pulao authentic indian food high quality",
        "Quinoa Pulao restaurant style plating",
    ],
    "masala dosa": [
        "Masala Dosa south indian dish real photo",
        "Masala Dosa restaurant style plating",
    ],
    "mini idli sambar": [
        "Idli Sambar south indian dish real photo",
        "Mini Idli Sambar restaurant style plating",
    ],
    "curd rice": [
        "Curd Rice south indian dish real photo",
        "Curd Rice restaurant style plating",
    ],
    "tandoori broccoli": [
        "Tandoori Broccoli restaurant style plating",
        "Broccoli healthy meal high quality",
    ],
    "fruit salad": [
        "Fruit Salad restaurant style plating",
        "Fruit Salad healthy meal high quality",
    ],
    "badam milk": [
        "Badam Milk restaurant style plating",
        "Badam Milk indian drink high quality",
    ],
    "lean chicken bowl": [
        "Chicken Bowl healthy meal restaurant style",
        "Chicken Rice Bowl high quality food photo",
    ],
    "tofu stir fry": [
        "Tofu Stir Fry restaurant style plating",
        "Tofu Stir Fry healthy meal high quality",
    ],
    "avocado millet salad": [
        "Avocado Millet Salad restaurant style plating",
        "Avocado Millet Salad healthy meal high quality",
    ],
    "egg white wrap": [
        "Egg White Wrap restaurant style plating",
        "Egg Wrap healthy meal high quality",
    ],
    "oats smoothie": [
        "Oats Smoothie restaurant style plating",
        "Oats Smoothie healthy drink high quality",
    ],
    "salmon rice bowl": [
        "Salmon Rice Bowl restaurant style plating",
        "Salmon Bowl healthy meal high quality",
    ],
    "paneer burrito bowl": [
        "Paneer Burrito Bowl restaurant style plating",
        "Paneer Bowl high quality food photo",
    ],
    "sweet potato chaat": [
        "Sweet Potato Chaat authentic indian food high quality",
        "Sweet Potato Chaat restaurant style plating",
    ],
    "turkey sandwich": [
        "Turkey Sandwich restaurant style plating",
        "Turkey Sandwich high quality food photo",
    ],
    "greek yogurt parfait": [
        "Greek Yogurt Parfait restaurant style plating",
        "Greek Yogurt Parfait healthy meal high quality",
    ],
}


def _load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _token_set(text):
    return set(_normalize(text).split())


def _score_result(food_name, result_title):
    food_tokens = _token_set(food_name)
    title_tokens = _token_set(result_title)
    if not food_tokens:
        return 0
    overlap = len(food_tokens & title_tokens)
    exact_bonus = 3 if _normalize(food_name) == _normalize(result_title) else 0
    return overlap + exact_bonus


def _search_spoonacular(query, cache_key):
    cache = _load_cache()
    if cache_key in cache:
        return cache[cache_key]

    api_key = current_app.config.get("SPOONACULAR_API_KEY", "")
    if not api_key:
        return []

    try:
        response = requests.get(
            SPOONACULAR_SEARCH_URL,
            params={
                "query": query,
                "number": 1,
                "apiKey": api_key,
                "addRecipeInformation": False,
            },
            timeout=12,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
    except requests.RequestException:
        return []

    cache[cache_key] = results
    _save_cache(cache)
    return results


def _placeholder_image():
    return "/static/img/food-placeholder.svg"


def get_food_image(food_name, used_recipe_ids=None):
    used_recipe_ids = used_recipe_ids if used_recipe_ids is not None else set()
    normalized = _normalize(food_name)
    queries = FOOD_QUERY_HINTS.get(normalized, []) + [
        f"{food_name} authentic indian food high quality",
        f"{food_name} restaurant style plating",
        f"{food_name} real food photo",
    ]

    best_match = None
    best_score = -1
    for index, query in enumerate(queries):
        results = _search_spoonacular(query, f"food::{normalized}::{index}")
        if not results:
            continue

        result = results[0]
        recipe_id = result.get("id")
        if recipe_id in used_recipe_ids:
            continue

        score = _score_result(food_name, result.get("title", ""))
        if score > best_score:
            best_match = result
            best_score = score

        if score >= max(2, len(_token_set(food_name))):
            break

    if not best_match:
        return _placeholder_image()

    recipe_id = best_match.get("id")
    if recipe_id is not None:
        used_recipe_ids.add(recipe_id)
    return best_match.get("image") or _placeholder_image()


def fetch_food_image(food_name, used_photo_ids=None):
    return get_food_image(food_name, used_photo_ids)


def fetch_restaurant_image(restaurant_name, city, used_photo_ids=None):
    return themed_restaurant_image(f"{restaurant_name} {city}")
