from collections import Counter

from ..models import MenuItem, Order


DIET_RULES = {
    "weight_loss": {
        "recommended_categories": {"diet", "protein", "balanced"},
        "avoid_categories": {"fast food", "dessert"},
        "food_type": None,
        "label": "Weight Loss",
        "diet_label": "balanced",
    },
    "muscle_gain": {
        "recommended_categories": {"protein", "balanced"},
        "avoid_categories": {"dessert"},
        "food_type": None,
        "label": "Muscle Gain",
        "diet_label": "high-protein",
    },
    "balanced_diet": {
        "recommended_categories": {"balanced", "diet", "protein"},
        "avoid_categories": set(),
        "food_type": None,
        "label": "Balanced Diet",
        "diet_label": "balanced",
    },
    "vegetarian": {
        "recommended_categories": {"diet", "balanced", "protein"},
        "avoid_categories": {"fast food"},
        "food_type": "veg",
        "label": "Vegetarian",
        "diet_label": "vegetarian",
    },
    "diabetic_friendly": {
        "recommended_categories": {"diet", "protein", "balanced"},
        "avoid_categories": {"fast food", "dessert"},
        "food_type": None,
        "label": "Diabetic Friendly",
        "diet_label": "diabetic-friendly",
    },
    "high_protein": {
        "recommended_categories": {"protein", "balanced"},
        "avoid_categories": {"dessert"},
        "food_type": None,
        "label": "High Protein",
        "diet_label": "high-protein",
    },
    "low_carb": {
        "recommended_categories": {"diet", "protein"},
        "avoid_categories": {"fast food"},
        "food_type": None,
        "label": "Low Carb",
        "diet_label": "low-carb",
    },
}

BEHAVIOR_RULES = {
    "biryani": ["Paneer Tikka", "Grilled Fish", "Veg Thali"],
    "dosa": ["Protein Idli Plate", "Ragi Dosa", "Veg Salad"],
    "thali": ["Millet Khichdi", "Paneer Tikka", "Veg Salad"],
    "fish": ["Grilled Fish", "Veg Salad", "Millet Khichdi"],
    "haleem": ["Chicken Dum Biryani", "Paneer Tikka", "Veg Thali"],
}

HIGH_PROTEIN_KEYWORDS = {"chicken", "fish", "paneer", "protein", "egg", "mutton"}


def build_diet_recommendation(goal, allergy_filter=""):
    rule = DIET_RULES.get(goal, DIET_RULES["balanced_diet"])
    query = MenuItem.query
    if rule["food_type"]:
        query = query.filter_by(food_type=rule["food_type"])

    recommended = []
    for item in query.order_by(MenuItem.healthy_badge.desc(), MenuItem.calories.asc()).all():
        nutrition = getattr(item, "nutrition", None)
        labels = nutrition_labels(item)
        allergens = nutrition_allergens(item)
        if allergy_filter and allergy_filter.lower() in allergens:
            continue
        if item.category in rule["recommended_categories"] or rule["diet_label"] in labels:
            recommended.append(item)

    avoid = []
    for item in MenuItem.query.order_by(MenuItem.calories.desc()).all():
        labels = nutrition_labels(item)
        allergens = nutrition_allergens(item)
        if allergy_filter and allergy_filter.lower() in allergens:
            continue
        if item.category in rule["avoid_categories"] and rule["diet_label"] not in labels:
            avoid.append(item)

    return {
        "goal": rule["label"],
        "recommended": [
            {"item": item, "reason": explain_diet_match(item, goal), "tags": menu_item_tags(item)}
            for item in recommended[:6]
        ],
        "avoid": [
            {"item": item, "reason": explain_avoid_match(item, goal), "tags": menu_item_tags(item)}
            for item in avoid[:5]
        ],
    }


def history_based_recommendations(user_id):
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).limit(10).all()
    keyword_counter = Counter()
    for order in orders:
        for order_item in order.order_items:
            lowered = order_item.menu_item.name.lower()
            for keyword in BEHAVIOR_RULES:
                if keyword in lowered:
                    keyword_counter[keyword] += order_item.quantity

    if not keyword_counter:
        return MenuItem.query.filter_by(healthy_badge=True).order_by(MenuItem.calories.asc()).limit(6).all()

    recommended_names = []
    for keyword, _count in keyword_counter.most_common(2):
        recommended_names.extend(BEHAVIOR_RULES[keyword])

    unique_names = list(dict.fromkeys(recommended_names))
    return MenuItem.query.filter(MenuItem.name.in_(unique_names)).limit(6).all()


def nutrition_labels(item):
    nutrition = getattr(item, "nutrition", None)
    if not nutrition or not nutrition.diet_labels:
        return set()
    return {label.strip().lower() for label in nutrition.diet_labels.split(",") if label.strip()}


def nutrition_allergens(item):
    nutrition = getattr(item, "nutrition", None)
    if not nutrition or not nutrition.allergens:
        return set()
    return {label.strip().lower() for label in nutrition.allergens.split(",") if label.strip()}


def menu_item_tags(item):
    tags = []
    lowered = item.name.lower()
    labels = nutrition_labels(item)
    allergens = nutrition_allergens(item)
    if item.healthy_badge or item.category == "diet":
        tags.append("Healthy")
    if item.category == "protein" or any(keyword in lowered for keyword in HIGH_PROTEIN_KEYWORDS) or "high-protein" in labels:
        tags.append("High Protein")
    if item.calories is not None and item.calories <= 250:
        tags.append("Low Calorie")
    if "diabetic-friendly" in labels:
        tags.append("Diabetic Friendly")
    if "low-carb" in labels:
        tags.append("Low Carb")
    if allergens and "none" not in allergens:
        tags.append("Allergy Aware")
    if is_popular_item(item):
        tags.append("Popular")
    return tags


def is_popular_item(item):
    lowered = item.name.lower()
    return item.restaurant.rating >= 4.6 or any(keyword in lowered for keyword in {"biryani", "dosa", "haleem"})


def explain_diet_match(item, goal):
    if goal == "weight_loss":
        return f"{item.name} is a lighter choice with about {item.calories or 'balanced'} kcal."
    if goal == "muscle_gain":
        return f"{item.name} supports muscle gain with stronger protein-focused ingredients."
    if goal == "vegetarian":
        return f"{item.name} keeps your meal vegetarian while still helping your nutrition goals."
    if goal == "diabetic_friendly":
        return f"{item.name} leans toward steadier carbs and better balance for diabetic-friendly eating."
    if goal == "high_protein":
        return f"{item.name} delivers stronger protein density for recovery and fuller meals."
    if goal == "low_carb":
        return f"{item.name} keeps carbs lower while still staying satisfying."
    return f"{item.name} fits a balanced plate with supportive nutrition and smart calories."


def explain_avoid_match(item, goal):
    if goal == "weight_loss":
        return f"{item.name} is better limited because it is more calorie-dense for weight loss."
    if goal == "muscle_gain":
        return f"{item.name} is less useful for muscle gain because it offers fewer quality nutrients."
    if goal == "diabetic_friendly":
        return f"{item.name} is better limited because it can spike carbs faster than the stronger matches above."
    if goal == "low_carb":
        return f"{item.name} is a less ideal fit because it leans higher on carbs."
    return f"{item.name} is better enjoyed occasionally compared with the stronger matches above."
