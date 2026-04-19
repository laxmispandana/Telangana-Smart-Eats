from collections import Counter

from ..models import MenuItem, Order


DIET_RULES = {
    "weight_loss": {
        "recommended_categories": {"diet", "protein", "balanced"},
        "avoid_categories": {"fast food", "dessert"},
        "food_type": None,
        "label": "Weight Loss",
    },
    "muscle_gain": {
        "recommended_categories": {"protein", "balanced"},
        "avoid_categories": {"dessert"},
        "food_type": None,
        "label": "Muscle Gain",
    },
    "balanced_diet": {
        "recommended_categories": {"balanced", "diet", "protein"},
        "avoid_categories": set(),
        "food_type": None,
        "label": "Balanced Diet",
    },
    "vegetarian": {
        "recommended_categories": {"diet", "balanced", "protein"},
        "avoid_categories": {"fast food"},
        "food_type": "veg",
        "label": "Vegetarian",
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


def build_diet_recommendation(goal):
    rule = DIET_RULES.get(goal, DIET_RULES["balanced_diet"])
    query = MenuItem.query
    if rule["food_type"]:
        query = query.filter_by(food_type=rule["food_type"])

    recommended = (
        query.filter(MenuItem.category.in_(rule["recommended_categories"]))
        .order_by(MenuItem.healthy_badge.desc(), MenuItem.calories.asc())
        .limit(6)
        .all()
    )
    avoid = (
        MenuItem.query.filter(MenuItem.category.in_(rule["avoid_categories"]))
        .order_by(MenuItem.calories.desc())
        .limit(5)
        .all()
    )
    return {
        "goal": rule["label"],
        "recommended": [
            {"item": item, "reason": explain_diet_match(item, goal), "tags": menu_item_tags(item)}
            for item in recommended
        ],
        "avoid": [
            {"item": item, "reason": explain_avoid_match(item, goal), "tags": menu_item_tags(item)}
            for item in avoid
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


def menu_item_tags(item):
    tags = []
    lowered = item.name.lower()
    if item.healthy_badge or item.category == "diet":
        tags.append("Healthy 🥗")
    if item.category == "protein" or any(keyword in lowered for keyword in HIGH_PROTEIN_KEYWORDS):
        tags.append("High Protein 💪")
    if item.calories is not None and item.calories <= 250:
        tags.append("Low Calorie 🔻")
    if is_popular_item(item):
        tags.append("Popular 🔥")
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
    return f"{item.name} fits a balanced plate with supportive nutrition and smart calories."


def explain_avoid_match(item, goal):
    if goal == "weight_loss":
        return f"{item.name} is better limited because it is more calorie-dense for weight loss."
    if goal == "muscle_gain":
        return f"{item.name} is less useful for muscle gain because it offers fewer quality nutrients."
    return f"{item.name} is better enjoyed occasionally compared with the stronger matches above."
