from collections import Counter, defaultdict
from math import atan2, cos, radians, sin, sqrt

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
    "pizza": ["Garlic Bread", "Caesar Salad", "Paneer Shawarma"],
    "biryani": ["Tandoori Chicken", "Green Salad Platter", "Double Ka Meetha"],
    "salad": ["Greek Yogurt Parfait", "Cold-Pressed Juice", "Lean Chicken Bowl"],
    "roll": ["BBQ Chicken Wings", "Choco Mousse", "Brown Rice Bowl"],
    "dosa": ["Mini Idli Sambar", "Cold-Pressed Juice", "Protein Idli Plate"],
    "bowl": ["Greek Yogurt Parfait", "Caesar Salad", "Paneer Protein Bowl"],
}


HIGH_PROTEIN_KEYWORDS = {
    "chicken",
    "egg",
    "fish",
    "paneer",
    "protein",
    "tofu",
    "turkey",
    "salmon",
    "mutton",
}


def haversine_distance(lat1, lon1, lat2, lon2):
    radius = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius * c


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
            {
                "item": item,
                "reason": explain_diet_match(item, goal),
                "tags": menu_item_tags(item),
            }
            for item in recommended
        ],
        "avoid": [
            {
                "item": item,
                "reason": explain_avoid_match(item, goal),
                "tags": menu_item_tags(item),
            }
            for item in avoid
        ],
    }


def _collect_order_item_ids(orders):
    sequences = []
    for order in orders:
        sequences.append([order_item.menu_item_id for order_item in order.order_items])
    return sequences


def people_also_ordered(menu_item_ids, limit=6):
    if not menu_item_ids:
        return []

    counter = Counter()
    orders = Order.query.order_by(Order.created_at.desc()).limit(200).all()
    for item_ids in _collect_order_item_ids(orders):
        current = set(item_ids)
        if current.intersection(menu_item_ids):
            for item_id in current:
                if item_id not in menu_item_ids:
                    counter[item_id] += 1

    if not counter:
        return []

    ranked_ids = [item_id for item_id, _count in counter.most_common(limit)]
    items = MenuItem.query.filter(MenuItem.id.in_(ranked_ids)).all()
    order_map = {item_id: index for index, item_id in enumerate(ranked_ids)}
    return sorted(items, key=lambda item: order_map.get(item.id, 999))


def history_based_recommendations(user_id):
    orders = (
        Order.query.filter_by(user_id=user_id)
        .order_by(Order.created_at.desc())
        .limit(12)
        .all()
    )
    keyword_counter = Counter()
    recent_item_ids = []
    for order in orders:
        for order_item in order.order_items:
            recent_item_ids.append(order_item.menu_item_id)
            name = order_item.menu_item.name.lower()
            for keyword in BEHAVIOR_RULES:
                if keyword in name:
                    keyword_counter[keyword] += order_item.quantity

    if not keyword_counter and not recent_item_ids:
        return (
            MenuItem.query.filter(MenuItem.healthy_badge.is_(True))
            .order_by(MenuItem.calories.asc())
            .limit(6)
            .all()
        )

    hybrid_names = []
    for keyword, _count in keyword_counter.most_common(2):
        hybrid_names.extend(BEHAVIOR_RULES[keyword])

    collaborative_items = people_also_ordered(set(recent_item_ids), limit=4)
    collaborative_ids = {item.id for item in collaborative_items}

    seen_names = set()
    ordered_names = []
    for name in hybrid_names:
        if name not in seen_names:
            seen_names.add(name)
            ordered_names.append(name)

    rule_based_items = MenuItem.query.filter(MenuItem.name.in_(ordered_names)).limit(6).all()
    merged = collaborative_items + [item for item in rule_based_items if item.id not in collaborative_ids]
    return merged[:6]


def menu_item_tags(menu_item):
    tags = []
    lowered_name = menu_item.name.lower()
    if menu_item.healthy_badge or menu_item.category == "diet":
        tags.append("Healthy 🥗")
    if menu_item.category == "protein" or any(
        keyword in lowered_name for keyword in HIGH_PROTEIN_KEYWORDS
    ):
        tags.append("High Protein 💪")
    if menu_item.calories is not None and menu_item.calories <= 250:
        tags.append("Low Calorie 🔻")
    if is_popular_item(menu_item):
        tags.append("Popular 🔥")
    return tags


def is_popular_item(menu_item):
    lowered_name = menu_item.name.lower()
    return menu_item.restaurant.rating >= 4.6 or any(
        keyword in lowered_name for keyword in {"biryani", "pizza", "haleem", "dosa"}
    )


def explain_diet_match(menu_item, goal):
    if goal == "weight_loss":
        return f"{menu_item.name} stays lighter at about {menu_item.calories or 'balanced'} kcal and fits a cleaner plate."
    if goal == "muscle_gain":
        return f"{menu_item.name} supports muscle gain with stronger protein-focused ingredients."
    if goal == "vegetarian":
        return f"{menu_item.name} keeps your meal vegetarian while still covering nutrition goals."
    return f"{menu_item.name} offers a balanced choice with smart calories and supportive nutrients."


def explain_avoid_match(menu_item, goal):
    if goal == "weight_loss":
        return f"{menu_item.name} is better limited because it is more calorie-dense for a weight-loss goal."
    if goal == "muscle_gain":
        return f"{menu_item.name} is less useful for muscle gain because it gives fewer quality nutrients."
    return f"{menu_item.name} is better enjoyed occasionally compared with the stronger matches above."
