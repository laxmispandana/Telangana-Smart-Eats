from flask import current_app

from .dynamic_images import fetch_food_image, fetch_restaurant_image
from .image_utils import themed_food_image, themed_restaurant_image
from ..extensions import db
from ..models import MenuItem, Restaurant


RESTAURANTS = [
    {
        "name": "Hyderabad Spice Route",
        "city": "Hyderabad",
        "area": "Banjara Hills",
        "lat": 17.4126,
        "lng": 78.4347,
        "rating": 4.7,
        "category": "non-veg",
        "cuisine": "Hyderabadi, Mughlai, Grills",
        "delivery_time": 28,
        "description": "Signature biryanis, grills, and hearty Telangana specials.",
        "menu": [
            ("Chicken Dum Biryani", 280, "protein", "non-veg", 620, False),
            ("Mutton Haleem Bowl", 260, "protein", "non-veg", 540, False),
            ("Tandoori Chicken", 320, "protein", "non-veg", 480, True),
            ("Talawa Gosht", 340, "fast food", "non-veg", 700, False),
            ("Garlic Butter Naan", 70, "fast food", "veg", 210, False),
            ("Paneer Tikka", 260, "protein", "veg", 350, True),
            ("Green Salad Platter", 150, "diet", "veg", 140, True),
            ("Millet Khichdi", 190, "diet", "veg", 280, True),
            ("Egg Fried Rice", 210, "fast food", "non-veg", 460, False),
            ("Double Ka Meetha", 120, "dessert", "veg", 330, False),
        ],
    },
    {
        "name": "Warangal Millet Kitchen",
        "city": "Warangal",
        "area": "Hanamkonda",
        "lat": 18.0057,
        "lng": 79.5575,
        "rating": 4.6,
        "category": "diet",
        "cuisine": "Healthy, Millet, South Indian",
        "delivery_time": 24,
        "description": "A healthy-first kitchen focused on millet bowls and balanced meals.",
        "menu": [
            ("Foxtail Millet Bowl", 220, "diet", "veg", 320, True),
            ("Protein Idli Plate", 160, "protein", "veg", 260, True),
            ("Grilled Fish with Greens", 340, "protein", "non-veg", 390, True),
            ("Low-Oil Chicken Curry", 290, "protein", "non-veg", 410, True),
            ("Ragi Dosa", 170, "diet", "veg", 240, True),
            ("Yogurt Fruit Cup", 110, "diet", "veg", 130, True),
            ("Peanut Chutney Wrap", 180, "diet", "veg", 290, True),
            ("Power Upma", 140, "balanced", "veg", 250, True),
            ("Paneer Protein Bowl", 260, "protein", "veg", 360, True),
            ("Cold-Pressed Juice", 90, "diet", "veg", 95, True),
        ],
    },
    {
        "name": "Karimnagar Grill House",
        "city": "Karimnagar",
        "area": "Mukarampura",
        "lat": 18.4386,
        "lng": 79.1288,
        "rating": 4.4,
        "category": "non-veg",
        "cuisine": "Grills, Fast Food, Rolls",
        "delivery_time": 30,
        "description": "Popular grill house with smoky kebabs, rolls, and comfort food.",
        "menu": [
            ("Peri Peri Chicken Roll", 190, "fast food", "non-veg", 420, False),
            ("BBQ Chicken Wings", 230, "fast food", "non-veg", 460, False),
            ("Paneer Shawarma", 180, "fast food", "veg", 380, False),
            ("Veg Loaded Pizza", 260, "fast food", "veg", 560, False),
            ("Chicken Loaded Pizza", 320, "fast food", "non-veg", 690, False),
            ("Garlic Bread", 120, "fast food", "veg", 270, False),
            ("Caesar Salad", 170, "diet", "veg", 210, True),
            ("Grilled Chicken Steak", 310, "protein", "non-veg", 370, True),
            ("Brown Rice Bowl", 200, "balanced", "veg", 300, True),
            ("Choco Mousse", 130, "dessert", "veg", 350, False),
        ],
    },
    {
        "name": "Nizamabad Veggie Craft",
        "city": "Nizamabad",
        "area": "Tilak Gardens",
        "lat": 18.6725,
        "lng": 78.0941,
        "rating": 4.5,
        "category": "veg",
        "cuisine": "Pure Veg, Tiffins, Diet Meals",
        "delivery_time": 22,
        "description": "Pure vegetarian kitchen with diet-friendly bowls and family meals.",
        "menu": [
            ("Veg Thali", 210, "balanced", "veg", 480, True),
            ("Palak Paneer", 240, "protein", "veg", 330, True),
            ("Mixed Veg Curry", 190, "balanced", "veg", 260, True),
            ("Quinoa Pulao", 230, "diet", "veg", 290, True),
            ("Masala Dosa", 140, "fast food", "veg", 350, False),
            ("Mini Idli Sambar", 130, "balanced", "veg", 220, True),
            ("Curd Rice", 120, "balanced", "veg", 250, True),
            ("Tandoori Broccoli", 170, "diet", "veg", 180, True),
            ("Fruit Salad", 100, "diet", "veg", 110, True),
            ("Badam Milk", 90, "dessert", "veg", 160, False),
        ],
    },
    {
        "name": "Khammam Fit Feast",
        "city": "Khammam",
        "area": "Wyra Road",
        "lat": 17.2473,
        "lng": 80.1514,
        "rating": 4.8,
        "category": "diet",
        "cuisine": "Diet, Protein, Bowls",
        "delivery_time": 26,
        "description": "Fitness-oriented meals, lean protein bowls, and calorie-conscious plates.",
        "menu": [
            ("Lean Chicken Bowl", 310, "protein", "non-veg", 380, True),
            ("Tofu Stir Fry", 240, "protein", "veg", 290, True),
            ("Avocado Millet Salad", 260, "diet", "veg", 250, True),
            ("Egg White Wrap", 180, "protein", "non-veg", 220, True),
            ("Oats Smoothie", 140, "diet", "veg", 190, True),
            ("Salmon Rice Bowl", 390, "protein", "non-veg", 430, True),
            ("Paneer Burrito Bowl", 280, "balanced", "veg", 340, True),
            ("Sweet Potato Chaat", 150, "diet", "veg", 170, True),
            ("Turkey Sandwich", 230, "protein", "non-veg", 310, True),
            ("Greek Yogurt Parfait", 130, "diet", "veg", 160, True),
        ],
    },
]


def seed_data():
    use_dynamic_images = bool(current_app.config.get("SPOONACULAR_API_KEY"))
    used_restaurant_photo_ids = set()
    used_food_photo_ids = set()

    if Restaurant.query.count() > 0:
        for restaurant in Restaurant.query.all():
            restaurant.image_url = (
                fetch_restaurant_image(
                    restaurant.name, restaurant.city, used_restaurant_photo_ids
                )
                if use_dynamic_images
                else themed_restaurant_image(f"{restaurant.name} {restaurant.city} dining")
            )
            for item in restaurant.menu_items:
                item.image_url = (
                    fetch_food_image(item.name, used_food_photo_ids)
                    if use_dynamic_images
                    else themed_food_image(item.name)
                )
        db.session.commit()
        return

    for restaurant_data in RESTAURANTS:
        restaurant = Restaurant(
            name=restaurant_data["name"],
            city=restaurant_data["city"],
            area=restaurant_data["area"],
            lat=restaurant_data["lat"],
            lng=restaurant_data["lng"],
            rating=restaurant_data["rating"],
            category=restaurant_data["category"],
            cuisine=restaurant_data["cuisine"],
            image_url=(
                fetch_restaurant_image(
                    restaurant_data["name"],
                    restaurant_data["city"],
                    used_restaurant_photo_ids,
                )
                if use_dynamic_images
                else themed_restaurant_image(
                    f"{restaurant_data['name']} {restaurant_data['city']} dining"
                )
            ),
            delivery_time=restaurant_data["delivery_time"],
            description=restaurant_data["description"],
        )
        db.session.add(restaurant)
        db.session.flush()

        for name, price, category, food_type, calories, healthy_badge in restaurant_data["menu"]:
            item = MenuItem(
                restaurant_id=restaurant.id,
                name=name,
                description=f"{name} prepared fresh at {restaurant.name}.",
                price=price,
                image_url=(
                    fetch_food_image(name, used_food_photo_ids)
                    if use_dynamic_images
                    else themed_food_image(name)
                ),
                category=category,
                food_type=food_type,
                calories=calories,
                healthy_badge=healthy_badge,
            )
            db.session.add(item)

    db.session.commit()
