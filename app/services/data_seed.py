from ..extensions import db
from ..models import Admin, MenuItem, Restaurant, Staff
from .image_utils import themed_food_image, themed_restaurant_image


RESTAURANTS = [
    {
        "name": "Paradise Biryani Hub",
        "city": "Hyderabad",
        "area": "Secunderabad",
        "lat": 17.4399,
        "lng": 78.4983,
        "rating": 4.8,
        "category": "mixed",
        "cuisine": "Hyderabadi, Biryani, Kebabs",
        "delivery_time": 29,
        "description": "A classic Hyderabad biryani stop with kebabs, curries, and fast-moving delivery.",
    },
    {
        "name": "Shah Ghouse Darbar",
        "city": "Hyderabad",
        "area": "Tolichowki",
        "lat": 17.4039,
        "lng": 78.4082,
        "rating": 4.7,
        "category": "mixed",
        "cuisine": "Mughlai, Hyderabadi, Haleem",
        "delivery_time": 31,
        "description": "Popular for haleem, biryani, grilled meats, and hearty Ramadan-style comfort food.",
    },
    {
        "name": "Bawarchi Express",
        "city": "Hyderabad",
        "area": "RTC X Roads",
        "lat": 17.4063,
        "lng": 78.4938,
        "rating": 4.6,
        "category": "mixed",
        "cuisine": "North Indian, Chinese, Telangana Meals",
        "delivery_time": 27,
        "description": "Multi-cuisine kitchen serving big portions and local favorites from central Hyderabad.",
    },
    {
        "name": "Kritunga Spice Kitchen",
        "city": "Warangal",
        "area": "Hanamkonda",
        "lat": 18.0055,
        "lng": 79.5578,
        "rating": 4.6,
        "category": "mixed",
        "cuisine": "Andhra, Telangana, Spicy Meals",
        "delivery_time": 24,
        "description": "Known for fiery Andhra curries, Telangana starters, and family-style meals.",
    },
    {
        "name": "Warangal Tiffin Corner",
        "city": "Warangal",
        "area": "Kazipet",
        "lat": 17.9894,
        "lng": 79.5270,
        "rating": 4.5,
        "category": "veg",
        "cuisine": "South Indian, Tiffins, Breakfast",
        "delivery_time": 20,
        "description": "Quick breakfast and tiffin kitchen for dosa, idli, and healthy millet specials.",
    },
    {
        "name": "Kakatiya Mess",
        "city": "Karimnagar",
        "area": "Mukarampura",
        "lat": 18.4389,
        "lng": 79.1282,
        "rating": 4.5,
        "category": "mixed",
        "cuisine": "Telangana Meals, Non-Veg Specials",
        "delivery_time": 23,
        "description": "Reliable local mess with biryani, fry curries, meals, and simple home-style food.",
    },
    {
        "name": "Karimnagar Grill House",
        "city": "Karimnagar",
        "area": "Jyothinagar",
        "lat": 18.4442,
        "lng": 79.1414,
        "rating": 4.4,
        "category": "mixed",
        "cuisine": "Grills, Rolls, Fast Food",
        "delivery_time": 26,
        "description": "Street-style grilled platters, wraps, and loaded fast food bowls.",
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
        "description": "Pure vegetarian kitchen with diet-friendly bowls, tiffins, and family combos.",
    },
    {
        "name": "Nizam Spice Pot",
        "city": "Nizamabad",
        "area": "Vinayak Nagar",
        "lat": 18.6845,
        "lng": 78.1078,
        "rating": 4.4,
        "category": "mixed",
        "cuisine": "Biryani, Fried Rice, Curries",
        "delivery_time": 28,
        "description": "Comfort food kitchen with biryani, Chinese-style rice, and curry combos.",
    },
    {
        "name": "Khammam Fit Feast",
        "city": "Khammam",
        "area": "Wyra Road",
        "lat": 17.2473,
        "lng": 80.1514,
        "rating": 4.6,
        "category": "mixed",
        "cuisine": "Healthy, Bowls, Protein Meals",
        "delivery_time": 21,
        "description": "Healthy kitchen serving grilled proteins, salads, millet bowls, and smoothies.",
    },
    {
        "name": "Khammam Chicken Junction",
        "city": "Khammam",
        "area": "Srinivasa Nagar",
        "lat": 17.2544,
        "lng": 80.1632,
        "rating": 4.3,
        "category": "mixed",
        "cuisine": "Chicken Specials, Rice Bowls, Snacks",
        "delivery_time": 25,
        "description": "Affordable chicken combos, bowls, and snack boxes for quick dinner orders.",
    },
]


BASE_MENU = [
    ("Chicken Dum Biryani", 280, "protein", "non-veg", 620, False),
    ("Mutton Haleem Bowl", 260, "protein", "non-veg", 540, False),
    ("Paneer Tikka", 240, "protein", "veg", 330, True),
    ("Masala Dosa", 140, "fast food", "veg", 350, False),
    ("Protein Idli Plate", 160, "protein", "veg", 260, True),
    ("Veg Thali", 210, "balanced", "veg", 480, True),
    ("Grilled Fish", 320, "protein", "non-veg", 390, True),
    ("Ragi Dosa", 170, "diet", "veg", 240, True),
    ("Veg Salad", 130, "diet", "veg", 110, True),
    ("Millet Khichdi", 190, "diet", "veg", 290, True),
]


def ensure_single_admin():
    if Admin.query.count() == 0:
        admin = Admin(
            name="FoodSprint Admin",
            email="admin@foodsprint.com",
            upi_id="admin@upi",
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()


def ensure_demo_staff():
    if Staff.query.count() == 0:
        staff = Staff(
            staff_id="STF001",
            name="FoodSprint Staff",
            email="staff@foodsprint.com",
        )
        staff.set_password("staff123")
        db.session.add(staff)
        db.session.commit()


def seed_data():
    ensure_single_admin()
    ensure_demo_staff()

    if Restaurant.query.count() > 0:
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
            image_url=themed_restaurant_image(
                f"{restaurant_data['name']} {restaurant_data['city']} restaurant"
            ),
            delivery_time=restaurant_data["delivery_time"],
            description=restaurant_data["description"],
        )
        db.session.add(restaurant)
        db.session.flush()

        for name, price, category, food_type, calories, healthy_badge in BASE_MENU:
            db.session.add(
                MenuItem(
                    restaurant_id=restaurant.id,
                    name=name,
                    description=f"{name} prepared fresh at {restaurant.name}.",
                    price=price,
                    image_url=themed_food_image(name),
                    category=category,
                    food_type=food_type,
                    calories=calories,
                    healthy_badge=healthy_badge,
                )
            )

    db.session.commit()
