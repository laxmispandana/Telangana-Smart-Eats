import json
from collections import defaultdict
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func

from .extensions import db
from .models import (
    Address,
    Admin,
    Favorite,
    LoyaltyEntry,
    MenuAvailability,
    MenuItem,
    NotificationLog,
    Order,
    OrderFulfillment,
    OrderItem,
    OrderItemCustomization,
    Payment,
    PromoCode,
    Restaurant,
    RestaurantProfile,
    Review,
    ReviewPhoto,
    Staff,
    SupportMessage,
    SupportTicket,
    User,
    UserReferral,
)
from .services.location import calculate_distance, fallback_city_coordinates
from .services.overpass import safe_fetch_overpass_restaurants
from .services.recommendations import build_diet_recommendation, history_based_recommendations, menu_item_tags
from .utils.payment import build_upi_payload, fake_transaction_id, generate_qr_data_uri

main_bp = Blueprint("main", __name__)
ORDER_STEPS = ["PLACED", "PREPARING", "OUT_FOR_DELIVERY", "DELIVERED"]
SPICE_LEVELS = ["Mild", "Medium", "Spicy", "Extra Spicy"]
RIDER_POOL = [
    ("Ravi", "+91-9876501001"),
    ("Anjali", "+91-9876501002"),
    ("Akhil", "+91-9876501003"),
]


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def current_admin():
    admin_id = session.get("admin_id")
    return db.session.get(Admin, admin_id) if admin_id else None


def current_staff():
    staff_id = session.get("staff_id")
    return db.session.get(Staff, staff_id) if staff_id else None


def login_required(view):
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)

    wrapped_view.__name__ = view.__name__
    return wrapped_view


def admin_required(view):
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in as admin.", "warning")
            return redirect(url_for("main.admin_login"))
        return view(*args, **kwargs)

    wrapped_view.__name__ = view.__name__
    return wrapped_view


def staff_required(view):
    def wrapped_view(*args, **kwargs):
        if "staff_id" not in session:
            flash("Please log in as staff.", "warning")
            return redirect(url_for("main.staff_login"))
        return view(*args, **kwargs)

    wrapped_view.__name__ = view.__name__
    return wrapped_view


def wants_json_response():
    return request.is_json or request.args.get("format") == "json" or request.accept_mimetypes.best == "application/json"


def parse_json_map(raw_value):
    if not raw_value:
        return {}
    try:
        return json.loads(raw_value)
    except (TypeError, ValueError):
        return {}


def split_csv(value):
    if not value:
        return []
    if isinstance(value, list):
        return [part.strip() for part in value if str(part).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def parse_option_choices(option):
    return [choice.strip() for choice in (option.choices or "").split("|") if choice.strip()]


def referral_code_for_user(user):
    return f"FS{user.id:04d}{user.name[:2].upper()}"


def ensure_user_referral(user, referred_by_code=None):
    referral = user.referral
    if referral:
        return referral
    referral = UserReferral(
        user_id=user.id,
        referral_code=referral_code_for_user(user),
        referred_by_code=(referred_by_code or "").strip().upper() or None,
    )
    db.session.add(referral)
    db.session.commit()
    return referral


def default_address_for_user(user_id):
    return (
        Address.query.filter_by(user_id=user_id)
        .order_by(Address.is_default.desc(), Address.id.asc())
        .first()
    )


def loyalty_balance(user_id):
    balance = db.session.query(func.coalesce(func.sum(LoyaltyEntry.points), 0)).filter_by(user_id=user_id).scalar()
    return int(balance or 0)


def successful_order_count(user_id):
    return Order.query.filter_by(user_id=user_id, payment_status="SUCCESS").count()


def user_favorite_ids(user_id):
    return {
        favorite.restaurant_id
        for favorite in Favorite.query.filter_by(user_id=user_id).all()
    }


def is_restaurant_open(profile):
    if not profile:
        return True
    try:
        opening = datetime.strptime(profile.opening_time or "09:00", "%H:%M").time()
        closing = datetime.strptime(profile.closing_time or "23:00", "%H:%M").time()
    except ValueError:
        return True
    now = datetime.now().time()
    if opening <= closing:
        return opening <= now <= closing
    return now >= opening or now <= closing


def restaurant_average_price(restaurant):
    prices = [item.price for item in restaurant.menu_items]
    return round(sum(prices) / len(prices), 2) if prices else 0


def restaurant_is_pure_veg(restaurant):
    return all(item.food_type.lower() == "veg" for item in restaurant.menu_items)


def restaurant_supports_food_type(restaurant, food_type):
    normalized = (food_type or "").strip().lower()
    if not normalized:
        return True
    item_types = {item.food_type.lower() for item in restaurant.menu_items}
    if normalized == "veg":
        return "veg" in item_types
    if normalized == "non-veg":
        return "non-veg" in item_types
    return normalized in item_types


def restaurant_delivery_fee(restaurant):
    return round((restaurant.profile.delivery_fee if restaurant.profile else 35), 2)


def restaurant_has_offer(restaurant):
    return bool(restaurant.profile and restaurant.profile.offers_text)


def serialize_restaurant_card(restaurant, user_lat=None, user_lon=None):
    distance_km = None
    if user_lat is not None and user_lon is not None:
        distance_km = round(calculate_distance(user_lat, user_lon, restaurant.lat, restaurant.lng), 2)

    path = url_for("main.restaurant_detail", restaurant_id=restaurant.id)
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "city": restaurant.city,
        "area": restaurant.area,
        "lat": restaurant.lat,
        "lon": restaurant.lng,
        "lng": restaurant.lng,
        "rating": restaurant.rating,
        "delivery_time": restaurant.delivery_time,
        "category": restaurant.category,
        "cuisine": restaurant.cuisine,
        "image_url": restaurant.image_url,
        "distance_km": distance_km,
        "avg_price": restaurant_average_price(restaurant),
        "delivery_fee": restaurant_delivery_fee(restaurant),
        "is_open_now": is_restaurant_open(restaurant.profile),
        "offers_text": restaurant.profile.offers_text if restaurant.profile else "",
        "pickup_enabled": bool(restaurant.profile and restaurant.profile.pickup_enabled),
        "has_veg": any(item.food_type.lower() == "veg" for item in restaurant.menu_items),
        "has_non_veg": any(item.food_type.lower() == "non-veg" for item in restaurant.menu_items),
        "is_pure_veg": restaurant_is_pure_veg(restaurant),
        "source": "catalog",
        "url": path,
    }


def get_cart():
    cart = session.setdefault("cart", {})
    if not isinstance(cart, dict):
        session["cart"] = {}
        return session["cart"]
    return cart


def normalize_cart_entry(entry):
    normalized = {
        "quantity": 0,
        "spice_level": "Medium",
        "removed_ingredients": "",
        "selected_addons": [],
        "combo_upgrade": "Regular",
        "allergy_note": "",
    }
    if isinstance(entry, int):
        normalized["quantity"] = entry
        return normalized
    if isinstance(entry, dict):
        normalized["quantity"] = int(entry.get("quantity", 0) or 0)
        normalized["spice_level"] = entry.get("spice_level") or "Medium"
        normalized["removed_ingredients"] = entry.get("removed_ingredients") or ""
        normalized["selected_addons"] = split_csv(entry.get("selected_addons"))
        normalized["combo_upgrade"] = entry.get("combo_upgrade") or "Regular"
        normalized["allergy_note"] = entry.get("allergy_note") or ""
    return normalized


def option_price_delta(item, customization):
    delta = 0
    for option in item.options:
        price_map = parse_json_map(option.price_delta_map)
        if option.option_type == "addon":
            for addon in customization["selected_addons"]:
                delta += float(price_map.get(addon, 0))
        elif option.option_type == "combo":
            delta += float(price_map.get(customization["combo_upgrade"], 0))
    return round(delta, 2)


def cart_entry_nutrition(item, customization, quantity):
    nutrition = getattr(item, "nutrition", None)
    base_protein = nutrition.protein_g if nutrition else 12
    base_carbs = nutrition.carbs_g if nutrition else 30
    base_fat = nutrition.fat_g if nutrition else 10
    extra_protein = 8 if "Extra Protein" in customization["selected_addons"] else 0
    extra_carbs = 6 if customization["combo_upgrade"] == "Meal Combo (+40)" else 15 if customization["combo_upgrade"] == "Family Combo (+120)" else 0
    extra_fat = 3 if "Extra Dip" in customization["selected_addons"] else 0
    calories = (item.calories or 240) + (80 if "Extra Protein" in customization["selected_addons"] else 0) + (120 if customization["combo_upgrade"] == "Meal Combo (+40)" else 260 if customization["combo_upgrade"] == "Family Combo (+120)" else 0)
    return {
        "protein_g": (base_protein + extra_protein) * quantity,
        "carbs_g": (base_carbs + extra_carbs) * quantity,
        "fat_g": (base_fat + extra_fat) * quantity,
        "calories": calories * quantity,
        "allergens": sorted({value.strip() for value in (nutrition.allergens.split(",") if nutrition and nutrition.allergens else ["none"]) if value.strip()}),
    }


def customization_summary(customization):
    bits = [customization["spice_level"]]
    if customization["selected_addons"]:
        bits.append("Add-ons: " + ", ".join(customization["selected_addons"]))
    if customization["combo_upgrade"] and customization["combo_upgrade"] != "Regular":
        bits.append(customization["combo_upgrade"])
    if customization["removed_ingredients"]:
        bits.append("No " + customization["removed_ingredients"])
    if customization["allergy_note"]:
        bits.append("Allergy: " + customization["allergy_note"])
    return " | ".join(bits)


def cart_context():
    cart = get_cart()
    entries = []
    total = 0
    count = 0
    protein_total = 0
    carbs_total = 0
    fat_total = 0
    calories_total = 0
    restaurants_in_cart = {}

    if not cart:
        return {
            "entries": [],
            "total": 0,
            "count": 0,
            "protein_total": 0,
            "carbs_total": 0,
            "fat_total": 0,
            "calories_total": 0,
            "restaurants": [],
        }

    item_ids = [int(item_id) for item_id in cart.keys()]
    items = MenuItem.query.filter(MenuItem.id.in_(item_ids)).all()
    for item in items:
        state = normalize_cart_entry(cart.get(str(item.id)))
        if state["quantity"] <= 0:
            continue
        unit_price = item.price + option_price_delta(item, state)
        subtotal = unit_price * state["quantity"]
        nutrition = cart_entry_nutrition(item, state, state["quantity"])
        total += subtotal
        count += state["quantity"]
        protein_total += nutrition["protein_g"]
        carbs_total += nutrition["carbs_g"]
        fat_total += nutrition["fat_g"]
        calories_total += nutrition["calories"]
        restaurants_in_cart[item.restaurant_id] = item.restaurant
        entries.append(
            {
                "menu_item": item,
                "quantity": state["quantity"],
                "subtotal": subtotal,
                "unit_price": unit_price,
                "customization": state,
                "customization_summary": customization_summary(state),
                "nutrition": nutrition,
            }
        )

    return {
        "entries": entries,
        "total": round(total, 2),
        "count": count,
        "protein_total": protein_total,
        "carbs_total": carbs_total,
        "fat_total": fat_total,
        "calories_total": calories_total,
        "restaurants": list(restaurants_in_cart.values()),
    }


def serialize_cart_response():
    cart_data = cart_context()
    return {
        "ok": True,
        "count": cart_data["count"],
        "total": round(cart_data["total"], 2),
        "protein_total": cart_data["protein_total"],
        "carbs_total": cart_data["carbs_total"],
        "fat_total": cart_data["fat_total"],
        "calories_total": cart_data["calories_total"],
        "entries": [
            {
                "item_id": entry["menu_item"].id,
                "name": entry["menu_item"].name,
                "price": round(entry["unit_price"], 2),
                "quantity": entry["quantity"],
                "subtotal": round(entry["subtotal"], 2),
                "image_url": entry["menu_item"].image_url,
                "restaurant_name": entry["menu_item"].restaurant.name,
                "customization_summary": entry["customization_summary"],
            }
            for entry in cart_data["entries"]
        ],
    }


def cart_delivery_fee(cart_data, fulfillment_mode):
    if fulfillment_mode == "pickup":
        return 0
    return round(sum(restaurant_delivery_fee(restaurant) for restaurant in cart_data["restaurants"]), 2)


def validate_promo(user, promo_code, subtotal):
    if not promo_code:
        return None, 0, None
    promo = PromoCode.query.filter(func.upper(PromoCode.code) == promo_code.upper(), PromoCode.active.is_(True)).first()
    if not promo:
        return None, 0, "Promo code not found."
    if subtotal < promo.min_order_amount:
        return None, 0, f"{promo.code} requires a minimum order of Rs. {promo.min_order_amount:.0f}."
    if promo.first_order_only and successful_order_count(user.id) > 0:
        return None, 0, f"{promo.code} is only available on your first paid order."
    return promo, promo.discount_value, None


def calculate_order_pricing(user, cart_data, fulfillment_mode, promo_code="", loyalty_to_use=0):
    subtotal = cart_data["total"]
    delivery_fee = cart_delivery_fee(cart_data, fulfillment_mode)
    promo, discount_amount, promo_error = validate_promo(user, promo_code, subtotal)
    if promo and promo.free_delivery:
        delivery_fee = 0
    loyalty_available = loyalty_balance(user.id)
    loyalty_to_use = max(0, min(int(loyalty_to_use or 0), loyalty_available))
    max_loyalty_usable = int(max(subtotal + delivery_fee - discount_amount, 0))
    loyalty_to_use = min(loyalty_to_use, max_loyalty_usable)
    total = max(subtotal + delivery_fee - discount_amount - loyalty_to_use, 0)
    earned = int(total // 20)
    return {
        "subtotal": subtotal,
        "delivery_fee": round(delivery_fee, 2),
        "discount_amount": round(discount_amount, 2),
        "promo": promo,
        "promo_error": promo_error,
        "loyalty_to_use": loyalty_to_use,
        "earned_points": earned,
        "total": round(total, 2),
    }


def next_staff_id():
    last_staff = Staff.query.order_by(Staff.id.desc()).first()
    next_number = 1 if not last_staff else int(last_staff.staff_id.replace("STF", "")) + 1
    return f"STF{next_number:03d}"


def log_notification(user_id, title, body, order=None, channels=None):
    for channel in channels or ["in_app"]:
        db.session.add(
            NotificationLog(
                user_id=user_id,
                order_id=order.id if order else None,
                channel=channel,
                title=title,
                body=body,
            )
        )


def verified_review_lookup(restaurant_id):
    verified = {}
    reviews = Review.query.filter_by(restaurant_id=restaurant_id).all()
    for review in reviews:
        verified[review.id] = Order.query.filter_by(user_id=review.user_id, payment_status="SUCCESS").join(OrderItem).join(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).count() > 0
    return verified


def can_cancel_order(order):
    return order.status not in {"DELIVERED", "CANCELLED"} and order.payment_status in {"PENDING", "SUCCESS"}


def restaurant_analytics(restaurants):
    analytics = []
    successful_orders = Order.query.filter_by(payment_status="SUCCESS").all()
    favorite_counts = defaultdict(int)
    for favorite in Favorite.query.all():
        favorite_counts[favorite.restaurant_id] += 1

    revenue_by_restaurant = defaultdict(float)
    order_counts = defaultdict(int)
    for order in successful_orders:
        seen = set()
        for order_item in order.order_items:
            revenue_by_restaurant[order_item.menu_item.restaurant_id] += order_item.price * order_item.quantity
            seen.add(order_item.menu_item.restaurant_id)
        for restaurant_id in seen:
            order_counts[restaurant_id] += 1

    for restaurant in restaurants:
        analytics.append(
            {
                "restaurant": restaurant,
                "orders": order_counts[restaurant.id],
                "revenue": round(revenue_by_restaurant[restaurant.id], 2),
                "favorites": favorite_counts[restaurant.id],
            }
        )
    return analytics


def build_checkout_summary(user):
    cart_data = cart_context()
    selected_mode = request.args.get("mode", "delivery")
    promo_code = request.args.get("promo_code", "")
    loyalty_to_use = request.args.get("loyalty_points", type=int) or 0
    pricing = calculate_order_pricing(user, cart_data, selected_mode, promo_code, loyalty_to_use)
    return cart_data, pricing, selected_mode


@main_bp.app_context_processor
def inject_globals():
    nav_user = current_user()
    return {
        "nav_user": nav_user,
        "nav_admin": current_admin(),
        "nav_staff": current_staff(),
        "cart_meta": cart_context(),
        "menu_item_tags": menu_item_tags,
        "order_steps": ORDER_STEPS,
        "is_restaurant_open": is_restaurant_open,
        "loyalty_points_balance": loyalty_balance(nav_user.id) if nav_user else 0,
    }


@main_bp.route("/")
def index():
    restaurants = Restaurant.query.order_by(Restaurant.rating.desc()).all()
    recommendations = (
        history_based_recommendations(session["user_id"])
        if "user_id" in session
        else MenuItem.query.order_by(MenuItem.healthy_badge.desc(), MenuItem.calories.asc()).limit(6).all()
    )
    top_rated = Restaurant.query.order_by(Restaurant.rating.desc()).limit(3).all()
    favorite_ids = user_favorite_ids(session["user_id"]) if "user_id" in session else set()
    fallback_city = fallback_city_coordinates("Hyderabad")
    return render_template(
        "index.html",
        restaurants=restaurants,
        recommendations=recommendations,
        top_rated=top_rated,
        favorite_ids=favorite_ids,
        promo_codes=PromoCode.query.filter_by(active=True).order_by(PromoCode.code.asc()).all(),
        fallback_city=fallback_city,
        city_options=sorted({restaurant.city for restaurant in restaurants}),
        osm_type_options=["restaurant", "cafe", "fast_food", "food_court"],
    )


@main_bp.route("/api/search")
def search_restaurants():
    query = request.args.get("q", "").strip().lower()
    restaurants = Restaurant.query.order_by(Restaurant.rating.desc()).all()
    filtered = [
        {
            "id": restaurant.id,
            "name": restaurant.name,
            "image": restaurant.image_url,
            "rating": restaurant.rating,
            "time": restaurant.delivery_time,
            "offers": restaurant.profile.offers_text if restaurant.profile else "",
        }
        for restaurant in restaurants
        if not query
        or query in restaurant.name.lower()
        or query in restaurant.city.lower()
        or query in restaurant.cuisine.lower()
    ]
    return jsonify(filtered)


@main_bp.route("/api/nearby")
def nearby_restaurants():
    city = request.args.get("city", "Hyderabad").strip().lower()
    restaurants = Restaurant.query.order_by(Restaurant.rating.desc()).all()
    filtered = [restaurant for restaurant in restaurants if restaurant.city.lower() == city]
    if not filtered:
        filtered = restaurants[:6]
    return jsonify(
        [
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "city": restaurant.city,
                "image": restaurant.image_url,
                "rating": restaurant.rating,
                "time": restaurant.delivery_time,
            }
            for restaurant in filtered
        ]
    )


@main_bp.route("/api/nearby-restaurants")
def nearby_restaurants_precise():
    user_lat = request.args.get("user_lat", type=float) or request.args.get("lat", type=float)
    user_lon = request.args.get("user_lon", type=float) or request.args.get("lon", type=float)
    selected_city = (request.args.get("city") or "").strip()
    food_type = (request.args.get("food_type") or "").strip().lower()
    osm_type = (request.args.get("type") or "").strip().lower()
    keyword = (request.args.get("keyword") or "").strip()
    max_distance_km = request.args.get("max_distance_km", default=10, type=float)
    min_rating = request.args.get("min_rating", type=float)
    open_now = request.args.get("open_now") == "1"
    free_delivery = request.args.get("free_delivery") == "1"
    budget_cap = request.args.get("budget_cap", type=float)
    pure_veg = request.args.get("pure_veg") == "1"
    fast_delivery = request.args.get("fast_delivery") == "1"
    offers_only = request.args.get("offers_only") == "1"
    limit = request.args.get("limit", default=10, type=int)

    restaurants = Restaurant.query.order_by(Restaurant.rating.desc()).all()
    if selected_city:
        restaurants = [restaurant for restaurant in restaurants if restaurant.city.lower() == selected_city.lower()]
    if food_type:
        restaurants = [restaurant for restaurant in restaurants if restaurant_supports_food_type(restaurant, food_type)]
    if keyword:
        lowered = keyword.lower()
        restaurants = [
            restaurant
            for restaurant in restaurants
            if lowered in restaurant.name.lower()
            or lowered in restaurant.cuisine.lower()
            or lowered in restaurant.area.lower()
        ]
    if open_now:
        restaurants = [restaurant for restaurant in restaurants if is_restaurant_open(restaurant.profile)]
    if free_delivery:
        restaurants = [restaurant for restaurant in restaurants if restaurant_delivery_fee(restaurant) == 0]
    if budget_cap:
        restaurants = [restaurant for restaurant in restaurants if restaurant_average_price(restaurant) <= budget_cap]
    if pure_veg:
        restaurants = [restaurant for restaurant in restaurants if restaurant_is_pure_veg(restaurant)]
    if fast_delivery:
        restaurants = [restaurant for restaurant in restaurants if restaurant.delivery_time <= 25]
    if offers_only:
        restaurants = [restaurant for restaurant in restaurants if restaurant_has_offer(restaurant)]

    fallback_city = fallback_city_coordinates(selected_city or "Hyderabad")
    reference_lat = user_lat if user_lat is not None else fallback_city["lat"]
    reference_lon = user_lon if user_lon is not None else fallback_city["lng"]

    catalog_places = [serialize_restaurant_card(restaurant, reference_lat, reference_lon) for restaurant in restaurants]
    catalog_places = [
        place for place in catalog_places
        if place["distance_km"] is None or place["distance_km"] <= max_distance_km
    ]
    if min_rating is not None:
        catalog_places = [place for place in catalog_places if place["rating"] is not None and place["rating"] >= min_rating]

    advanced_catalog_only = any([open_now, free_delivery, budget_cap, pure_veg, fast_delivery, offers_only])
    osm_places = []
    osm_error = None
    if not advanced_catalog_only:
        osm_places, osm_error = safe_fetch_overpass_restaurants(
            reference_lat,
            reference_lon,
            radius_m=max(1000, int(max_distance_km * 1000)),
            amenity=osm_type,
            keyword=keyword,
        )

        if food_type == "veg":
            osm_places = [
                place for place in osm_places
                if "veg" in (place.get("cuisine") or "").lower() or place["type"] == "cafe"
            ]
        elif food_type == "non-veg":
            osm_places = [
                place for place in osm_places
                if "veg" not in (place.get("cuisine") or "").lower()
            ]

    merged_places = catalog_places + [place for place in osm_places if place["distance_km"] <= max_distance_km]
    merged_places.sort(key=lambda item: ((item["distance_km"] if item["distance_km"] is not None else 99999), -(item.get("rating") or 0)))
    return jsonify(
        {
            "city": fallback_city["name"],
            "user_lat": reference_lat,
            "user_lon": reference_lon,
            "osm_error": osm_error,
            "restaurants": merged_places[: max(limit, 1)],
        }
    )


@main_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return redirect(url_for("main.signup"))

        user = User(
            name=request.form["name"].strip(),
            email=email,
            phone=request.form["phone"].strip(),
            location=request.form["location"].strip(),
        )
        user.set_password(request.form["password"])
        db.session.add(user)
        db.session.commit()
        ensure_user_referral(user, request.form.get("referral_code"))
        address = Address(
            user_id=user.id,
            label="Home",
            recipient_name=user.name,
            phone=user.phone,
            address_line=user.location,
            landmark="",
            city=user.location.split(",")[0].strip() if "," in user.location else user.location,
            delivery_notes="Call when arriving",
            is_default=True,
        )
        db.session.add(address)
        db.session.commit()
        session.clear()
        session["user_id"] = user.id
        flash("Welcome to FoodSprint. Your first address and referral wallet are ready.", "success")
        return redirect(url_for("main.index"))

    return render_template("signup.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if user and user.check_password(request.form["password"]):
            session.clear()
            session["user_id"] = user.id
            flash("Welcome back.", "success")
            return redirect(url_for("main.index"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")


@main_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("main.index"))


@main_bp.route("/account")
@login_required
def account():
    user = current_user()
    referral = ensure_user_referral(user)
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    favorites = (
        Restaurant.query.join(Favorite, Favorite.restaurant_id == Restaurant.id)
        .filter(Favorite.user_id == user.id)
        .order_by(Restaurant.rating.desc())
        .all()
    )
    tickets = SupportTicket.query.filter_by(user_id=user.id).order_by(SupportTicket.created_at.desc()).all()
    notifications = NotificationLog.query.filter_by(user_id=user.id).order_by(NotificationLog.created_at.desc()).limit(15).all()
    return render_template(
        "account.html",
        user=user,
        referral=referral,
        addresses=Address.query.filter_by(user_id=user.id).order_by(Address.is_default.desc(), Address.id.asc()).all(),
        orders=orders,
        favorites=favorites,
        loyalty_entries=LoyaltyEntry.query.filter_by(user_id=user.id).order_by(LoyaltyEntry.created_at.desc()).limit(20).all(),
        tickets=tickets,
        notifications=notifications,
        loyalty_total=loyalty_balance(user.id),
    )


@main_bp.route("/addresses/add", methods=["POST"])
@login_required
def add_address():
    user = current_user()
    is_default = request.form.get("is_default") == "on" or Address.query.filter_by(user_id=user.id).count() == 0
    if is_default:
        Address.query.filter_by(user_id=user.id, is_default=True).update({"is_default": False})
    address = Address(
        user_id=user.id,
        label=request.form["label"].strip() or "Address",
        recipient_name=request.form["recipient_name"].strip() or user.name,
        phone=request.form["phone"].strip() or user.phone,
        address_line=request.form["address_line"].strip(),
        landmark=request.form.get("landmark", "").strip(),
        city=request.form["city"].strip(),
        delivery_notes=request.form.get("delivery_notes", "").strip(),
        is_default=is_default,
    )
    db.session.add(address)
    db.session.commit()
    flash("Address saved.", "success")
    return redirect(request.referrer or url_for("main.account"))


@main_bp.route("/addresses/default/<int:address_id>", methods=["POST"])
@login_required
def set_default_address(address_id):
    address = Address.query.get_or_404(address_id)
    if address.user_id != session["user_id"]:
        flash("That address is not available for your account.", "danger")
        return redirect(url_for("main.account"))
    Address.query.filter_by(user_id=address.user_id, is_default=True).update({"is_default": False})
    address.is_default = True
    db.session.commit()
    flash("Default address updated.", "success")
    return redirect(request.referrer or url_for("main.account"))


@main_bp.route("/favorites/toggle/<int:restaurant_id>", methods=["POST"])
@login_required
def toggle_favorite(restaurant_id):
    favorite = Favorite.query.filter_by(user_id=session["user_id"], restaurant_id=restaurant_id).first()
    if favorite:
        db.session.delete(favorite)
        flash("Removed from favorites.", "info")
    else:
        db.session.add(Favorite(user_id=session["user_id"], restaurant_id=restaurant_id))
        flash("Added to favorites.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("main.index"))


@main_bp.route("/admin/register", methods=["GET", "POST"])
def admin_register():
    if Admin.query.count() >= 1:
        flash("Only one admin account is allowed in FoodSprint.", "warning")
        return redirect(url_for("main.admin_login"))

    if request.method == "POST":
        admin = Admin(
            name=request.form["name"].strip(),
            email=request.form["email"].strip().lower(),
            upi_id=current_app.config.get("FOODSPRINT_UPI_ID"),
        )
        admin.set_password(request.form["password"])
        db.session.add(admin)
        db.session.commit()
        session.clear()
        session["admin_id"] = admin.id
        flash("Admin account created.", "success")
        return redirect(url_for("main.admin_dashboard"))

    return render_template("admin_register.html")


@main_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin = Admin.query.filter_by(email=request.form["email"].strip().lower()).first()
        if admin and admin.check_password(request.form["password"]):
            session.clear()
            session["admin_id"] = admin.id
            flash("Admin logged in.", "success")
            return redirect(url_for("main.admin_dashboard"))
        flash("Invalid admin credentials.", "danger")
    return render_template("admin_login.html")


@main_bp.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("main.index"))


@main_bp.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
        staff = Staff.query.filter_by(email=request.form["email"].strip().lower()).first()
        if staff and staff.check_password(request.form["password"]):
            session.clear()
            session["staff_id"] = staff.id
            flash("Staff logged in.", "success")
            return redirect(url_for("main.staff_dashboard"))
        flash("Invalid staff credentials.", "danger")
    return render_template("staff_login.html")


@main_bp.route("/staff/logout")
def staff_logout():
    session.pop("staff_id", None)
    flash("Staff logged out.", "info")
    return redirect(url_for("main.index"))


@main_bp.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    admin = current_admin()
    restaurants = Restaurant.query.order_by(Restaurant.name.asc()).all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    staff_members = Staff.query.order_by(Staff.staff_id.asc()).all()
    recent_reviews = Review.query.order_by(Review.created_at.desc()).limit(8).all()
    support_tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).limit(12).all()
    return render_template(
        "admin_dashboard.html",
        admin=admin,
        restaurants=restaurants,
        recent_orders=orders,
        total_menu_items=MenuItem.query.count(),
        staff_members=staff_members,
        recent_reviews=recent_reviews,
        support_tickets=support_tickets,
        analytics=restaurant_analytics(restaurants),
        staff_limit=current_app.config["STAFF_LIMIT"],
    )


@main_bp.route("/admin/add_staff", methods=["POST"])
@admin_required
def add_staff():
    if Staff.query.count() >= current_app.config["STAFF_LIMIT"]:
        flash("Staff limit reached. Increase STAFF_LIMIT to add more accounts.", "danger")
        return redirect(url_for("main.admin_dashboard"))

    email = request.form["email"].strip().lower()
    if Staff.query.filter_by(email=email).first():
        flash("Staff account with that email already exists.", "danger")
        return redirect(url_for("main.admin_dashboard"))

    staff = Staff(
        staff_id=next_staff_id(),
        name=request.form["name"].strip(),
        email=email,
    )
    staff.set_password(request.form["password"])
    db.session.add(staff)
    db.session.commit()
    flash(f"Staff account {staff.staff_id} created.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/set_upi", methods=["POST"])
@admin_required
def set_upi():
    admin = current_admin()
    admin.upi_id = request.form["upi_id"].strip()
    db.session.commit()
    flash("UPI ID updated successfully.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/restaurant/<int:restaurant_id>/profile", methods=["POST"])
@admin_required
def update_restaurant_profile(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    profile = restaurant.profile or RestaurantProfile(restaurant_id=restaurant.id)
    db.session.add(profile)
    profile.delivery_fee = float(request.form.get("delivery_fee", profile.delivery_fee or 0))
    profile.min_order_amount = float(request.form.get("min_order_amount", profile.min_order_amount or 0))
    profile.opening_time = request.form.get("opening_time", profile.opening_time or "09:00")
    profile.closing_time = request.form.get("closing_time", profile.closing_time or "23:00")
    profile.pickup_enabled = request.form.get("pickup_enabled") == "on"
    profile.offers_text = request.form.get("offers_text", "").strip()
    profile.support_phone = request.form.get("support_phone", "").strip()
    db.session.commit()
    flash(f"{restaurant.name} business settings updated.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/menu/<int:item_id>", methods=["POST"])
@admin_required
def update_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.price = float(request.form.get("price", item.price))
    availability = item.availability or MenuAvailability(menu_item_id=item.id)
    db.session.add(availability)
    availability.is_available = request.form.get("is_available") == "on"
    availability.stock_count = int(request.form.get("stock_count", availability.stock_count or 0))
    db.session.commit()
    flash(f"{item.name} updated.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/support/<int:ticket_id>/reply", methods=["POST"])
@admin_required
def admin_reply_support(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    message = request.form.get("message", "").strip()
    if message:
        db.session.add(SupportMessage(ticket_id=ticket.id, sender_role="admin", message=message))
        log_notification(ticket.user_id, "Support replied", f"Support replied to ticket #{ticket.id}.", order=ticket.order)
        db.session.commit()
        flash("Support reply sent.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/support/<int:ticket_id>/status", methods=["POST"])
@admin_required
def admin_update_support_status(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    ticket.status = request.form.get("status", ticket.status).strip().upper()
    ticket.resolution_notes = request.form.get("resolution_notes", "").strip()
    db.session.commit()
    flash(f"Ticket #{ticket.id} updated.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/order/<int:order_id>/refund", methods=["POST"])
@admin_required
def admin_mark_refund(order_id):
    order = Order.query.get_or_404(order_id)
    order.payment_status = "REFUNDED"
    if order.latest_payment:
        order.latest_payment.status = "REFUNDED"
    log_notification(order.user_id, "Refund completed", f"Refund completed for order #{order.id}.", order=order, channels=["in_app", "email"])
    db.session.commit()
    flash(f"Refund marked for order #{order.id}.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/staff/dashboard")
@staff_required
def staff_dashboard():
    staff = current_staff()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    tickets = SupportTicket.query.filter(SupportTicket.status.in_(["OPEN", "ESCALATED"])).order_by(SupportTicket.created_at.desc()).all()
    return render_template("staff_dashboard.html", staff=staff, orders=orders, tickets=tickets)


@main_bp.route("/staff/update_order/<int:order_id>", methods=["POST"])
@staff_required
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status == "CANCELLED":
        flash("Cancelled orders cannot move forward.", "warning")
        return redirect(url_for("main.staff_dashboard"))
    try:
        current_index = ORDER_STEPS.index(order.status)
    except ValueError:
        current_index = 0
    if current_index < len(ORDER_STEPS) - 1:
        order.status = ORDER_STEPS[current_index + 1]
        fulfillment = order.fulfillment
        if fulfillment:
            if order.status == "PREPARING":
                fulfillment.eta_minutes = max(20, fulfillment.eta_minutes - 5)
            elif order.status == "OUT_FOR_DELIVERY":
                rider_name, rider_phone = RIDER_POOL[order.id % len(RIDER_POOL)]
                fulfillment.rider_name = rider_name
                fulfillment.rider_phone = rider_phone
                fulfillment.eta_minutes = max(12, fulfillment.eta_minutes - 10)
            elif order.status == "DELIVERED":
                fulfillment.eta_minutes = 0
        log_notification(
            order.user_id,
            f"Order #{order.id} is now {order.status.replace('_', ' ')}",
            f"Your order has moved to {order.status.replace('_', ' ').title()}.",
            order=order,
            channels=["in_app", "whatsapp", "sms"],
        )
        db.session.commit()
        flash(f"Order #{order.id} updated to {order.status.replace('_', ' ')}.", "success")
    else:
        flash("This order is already delivered.", "info")
    return redirect(url_for("main.staff_dashboard"))


@main_bp.route("/restaurants/<int:restaurant_id>")
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    available_menu = [item for item in restaurant.menu_items if not item.availability or item.availability.is_available]
    unavailable_menu = [item for item in restaurant.menu_items if item.availability and not item.availability.is_available]
    recommended_items = available_menu[:4]
    reviews = Review.query.filter_by(restaurant_id=restaurant.id).order_by(Review.created_at.desc()).all()
    verified_reviews = verified_review_lookup(restaurant.id)
    cart_quantities = {key: normalize_cart_entry(value)["quantity"] for key, value in get_cart().items()}
    is_favorite = "user_id" in session and restaurant.id in user_favorite_ids(session["user_id"])
    ordered_here = False
    if "user_id" in session:
        ordered_here = Order.query.filter_by(user_id=session["user_id"], payment_status="SUCCESS").join(OrderItem).join(MenuItem).filter(MenuItem.restaurant_id == restaurant.id).count() > 0
    return render_template(
        "restaurant_detail.html",
        restaurant=restaurant,
        menu_items=available_menu,
        unavailable_menu=unavailable_menu,
        recommended_items=recommended_items,
        reviews=reviews,
        verified_reviews=verified_reviews,
        cart_quantities=cart_quantities,
        is_favorite=is_favorite,
        ordered_here=ordered_here,
        spice_levels=SPICE_LEVELS,
    )


@main_bp.route("/restaurants/<int:restaurant_id>/reviews", methods=["POST"])
@login_required
def add_review(restaurant_id):
    review = Review(
        user_id=session["user_id"],
        restaurant_id=restaurant_id,
        rating=int(request.form["rating"]),
        comment=request.form["comment"].strip(),
    )
    db.session.add(review)
    db.session.flush()
    photo_url = request.form.get("photo_url", "").strip()
    if photo_url:
        db.session.add(ReviewPhoto(review_id=review.id, image_url=photo_url))
    db.session.commit()
    flash("Review submitted.", "success")
    return redirect(url_for("main.restaurant_detail", restaurant_id=restaurant_id))


@main_bp.route("/cart")
def cart():
    cart_data = cart_context()
    if wants_json_response():
        return jsonify(serialize_cart_response())
    return render_template("cart.html", cart_data=cart_data)


@main_bp.route("/cart/add", methods=["POST"])
def add_to_cart():
    payload = request.get_json(silent=True) or request.form
    item_id = payload.get("item_id")
    quantity = int(payload.get("quantity", 1) or 1)
    if not item_id:
        return redirect(url_for("main.cart"))
    item = MenuItem.query.get_or_404(int(item_id))
    if item.availability and not item.availability.is_available:
        if request.is_json:
            return jsonify({"ok": False, "message": "That item is out of stock."}), 400
        flash("That item is currently unavailable.", "danger")
        return redirect(request.referrer or url_for("main.restaurant_detail", restaurant_id=item.restaurant_id))
    cart = get_cart()
    existing = normalize_cart_entry(cart.get(str(item_id), {}))
    existing["quantity"] += quantity
    existing["spice_level"] = payload.get("spice_level") or existing["spice_level"]
    existing["removed_ingredients"] = payload.get("removed_ingredients") or existing["removed_ingredients"]
    existing["allergy_note"] = payload.get("allergy_note") or existing["allergy_note"]
    existing["combo_upgrade"] = payload.get("combo_upgrade") or existing["combo_upgrade"]
    existing["selected_addons"] = split_csv(payload.get("selected_addons")) or existing["selected_addons"]
    cart[str(item_id)] = existing
    session.modified = True
    if request.is_json:
        return jsonify(serialize_cart_response())
    flash("Item added to cart.", "success")
    return redirect(request.referrer or url_for("main.cart"))


@main_bp.route("/cart/update", methods=["POST"])
def update_cart():
    data = request.get_json(silent=True) or request.form
    item_id = data.get("item_id")
    quantity = int(data.get("quantity", 0) or 0)
    cart = get_cart()
    if quantity <= 0:
        cart.pop(str(item_id), None)
    else:
        existing = normalize_cart_entry(cart.get(str(item_id), {}))
        existing["quantity"] = quantity
        cart[str(item_id)] = existing
    session.modified = True
    if request.is_json:
        return jsonify(serialize_cart_response())
    return redirect(url_for("main.cart"))


@main_bp.route("/checkout")
@login_required
def checkout():
    user = current_user()
    admin = Admin.query.first()
    cart_data, pricing, selected_mode = build_checkout_summary(user)
    return render_template(
        "checkout.html",
        cart_data=cart_data,
        pricing=pricing,
        selected_mode=selected_mode,
        addresses=Address.query.filter_by(user_id=user.id).order_by(Address.is_default.desc(), Address.id.asc()).all(),
        default_address=default_address_for_user(user.id),
        admin_upi_id=admin.upi_id if admin else "",
        promo_codes=PromoCode.query.filter_by(active=True).order_by(PromoCode.code.asc()).all(),
        loyalty_total=loyalty_balance(user.id),
        default_schedule=(datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"),
    )


@main_bp.route("/payment/upi", methods=["POST"])
@login_required
def payment_upi():
    user = current_user()
    admin = Admin.query.first()
    if not admin or not admin.upi_id:
        flash("Admin UPI ID is not configured yet.", "danger")
        return redirect(url_for("main.checkout"))

    cart_data = cart_context()
    if cart_data["count"] == 0:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("main.cart"))

    fulfillment_mode = request.form.get("fulfillment_mode", "delivery")
    address_id = request.form.get("address_id", type=int)
    selected_address = default_address_for_user(user.id)
    if address_id:
        selected_address = Address.query.filter_by(id=address_id, user_id=user.id).first()
    if fulfillment_mode == "delivery" and not selected_address:
        flash("Please save a delivery address before checkout.", "warning")
        return redirect(url_for("main.checkout"))

    pricing = calculate_order_pricing(
        user,
        cart_data,
        fulfillment_mode,
        request.form.get("promo_code", "").strip(),
        request.form.get("loyalty_points", type=int) or 0,
    )
    if pricing["promo_error"]:
        flash(pricing["promo_error"], "danger")
        return redirect(url_for("main.checkout"))

    schedule_raw = request.form.get("scheduled_for", "").strip()
    scheduled_for = None
    if schedule_raw:
        try:
            scheduled_for = datetime.fromisoformat(schedule_raw)
        except ValueError:
            scheduled_for = None

    order = Order(
        user_id=user.id,
        total_amount=pricing["total"],
        status="PLACED",
        payment_status="PENDING",
    )
    db.session.add(order)
    db.session.flush()

    for entry in cart_data["entries"]:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=entry["menu_item"].id,
            quantity=entry["quantity"],
            price=entry["unit_price"],
        )
        db.session.add(order_item)
        db.session.flush()
        db.session.add(
            OrderItemCustomization(
                order_item_id=order_item.id,
                spice_level=entry["customization"]["spice_level"],
                removed_ingredients=entry["customization"]["removed_ingredients"],
                addon_names=", ".join(entry["customization"]["selected_addons"]),
                combo_upgrade=entry["customization"]["combo_upgrade"],
                allergy_note=entry["customization"]["allergy_note"],
            )
        )

    address_snapshot = None
    if selected_address:
        address_snapshot = f"{selected_address.label}: {selected_address.address_line}, {selected_address.city} ({selected_address.phone})"

    split_count = max(1, request.form.get("split_count", type=int) or 1)
    fulfillment = OrderFulfillment(
        order_id=order.id,
        fulfillment_mode=fulfillment_mode,
        scheduled_for=scheduled_for,
        address_snapshot=address_snapshot,
        delivery_notes=request.form.get("delivery_notes", "").strip() or (selected_address.delivery_notes if selected_address else ""),
        special_instructions=request.form.get("special_instructions", "").strip(),
        eta_minutes=max(18, sum(restaurant.delivery_time for restaurant in cart_data["restaurants"]) // max(len(cart_data["restaurants"]), 1)),
        split_count=split_count,
        split_amount=round(pricing["total"] / split_count, 2),
        promo_code=pricing["promo"].code if pricing["promo"] else None,
        discount_amount=pricing["discount_amount"],
        delivery_fee=pricing["delivery_fee"],
        loyalty_points_used=pricing["loyalty_to_use"],
        loyalty_points_earned=pricing["earned_points"],
    )
    db.session.add(fulfillment)

    payload = build_upi_payload(admin.upi_id, pricing["total"])
    qr_code = generate_qr_data_uri(payload)

    payment = Payment(
        order_id=order.id,
        method="UPI",
        status="PENDING",
        upi_id=admin.upi_id,
        qr_payload=payload,
    )
    db.session.add(payment)
    log_notification(user.id, "Payment initiated", f"UPI payment created for order #{order.id}.", order=order, channels=["in_app", "email"])
    db.session.commit()

    return render_template(
        "payment.html",
        qr_code=qr_code,
        upi_id=admin.upi_id,
        amount=pricing["total"],
        order=order,
        pricing=pricing,
        fulfillment=fulfillment,
    )


@main_bp.route("/payment/confirm", methods=["POST"])
@login_required
def payment_confirm():
    data = request.get_json(silent=True) or {}
    order = Order.query.get_or_404(data.get("order_id"))
    if order.user_id != session["user_id"]:
        return jsonify({"ok": False, "message": "Unauthorized"}), 403

    payment = order.latest_payment
    if not payment:
        return jsonify({"ok": False, "message": "Payment not found"}), 404

    payment.status = "SUCCESS"
    payment.transaction_id = fake_transaction_id()
    payment.created_at = datetime.utcnow()
    order.payment_status = "SUCCESS"
    if order.status == "PLACED":
        order.status = "PREPARING"

    fulfillment = order.fulfillment
    if fulfillment and fulfillment.loyalty_points_used:
        db.session.add(
            LoyaltyEntry(
                user_id=order.user_id,
                order_id=order.id,
                points=-abs(fulfillment.loyalty_points_used),
                reason=f"Redeemed on order #{order.id}",
            )
        )
    if fulfillment and fulfillment.loyalty_points_earned:
        db.session.add(
            LoyaltyEntry(
                user_id=order.user_id,
                order_id=order.id,
                points=fulfillment.loyalty_points_earned,
                reason=f"Earned from order #{order.id}",
            )
        )

    referral = UserReferral.query.filter_by(user_id=order.user_id).first()
    if referral and referral.referred_by_code and not referral.referral_rewarded:
        referrer = UserReferral.query.filter_by(referral_code=referral.referred_by_code).first()
        if referrer and referrer.user_id != order.user_id:
            db.session.add(LoyaltyEntry(user_id=order.user_id, order_id=order.id, points=50, reason="Referral reward"))
            db.session.add(LoyaltyEntry(user_id=referrer.user_id, order_id=order.id, points=50, reason="Referral bonus"))
            referral.referral_rewarded = True
            log_notification(referrer.user_id, "Referral reward unlocked", f"You earned 50 points from order #{order.id}.", order=order)

    log_notification(
        order.user_id,
        "Payment confirmed",
        f"Your payment for order #{order.id} is confirmed. Tracking is now live.",
        order=order,
        channels=["in_app", "email", "sms", "whatsapp"],
    )
    db.session.commit()
    session["cart"] = {}

    return jsonify({"ok": True, "redirect_url": url_for("main.order_detail", order_id=order.id)})


@main_bp.route("/payment/failure")
def payment_failure():
    order = None
    order_id = request.args.get("order_id", type=int)
    if order_id:
        order = Order.query.get(order_id)
        if order:
            order.payment_status = "FAILED"
            if order.latest_payment:
                order.latest_payment.status = "FAILED"
            db.session.commit()
    return render_template("payment_failure.html", order=order)


@main_bp.route("/order/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session["user_id"]:
        flash("That order is not available for your account.", "danger")
        return redirect(url_for("main.index"))
    tickets = SupportTicket.query.filter_by(order_id=order.id, user_id=order.user_id).order_by(SupportTicket.created_at.desc()).all()
    notifications = NotificationLog.query.filter_by(order_id=order.id).order_by(NotificationLog.created_at.desc()).all()
    return render_template(
        "order_tracking.html",
        order=order,
        tickets=tickets,
        notifications=notifications,
        can_cancel=can_cancel_order(order),
    )


@main_bp.route("/order/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session["user_id"]:
        flash("That order is not available for your account.", "danger")
        return redirect(url_for("main.index"))
    if not can_cancel_order(order):
        flash("This order can no longer be cancelled.", "warning")
        return redirect(url_for("main.order_detail", order_id=order.id))
    order.status = "CANCELLED"
    if order.payment_status == "SUCCESS":
        order.payment_status = "REFUND_PENDING"
        if order.latest_payment:
            order.latest_payment.status = "REFUND_PENDING"
    ticket = SupportTicket(
        user_id=order.user_id,
        order_id=order.id,
        subject="Cancellation and refund request",
        issue_type="refund",
        message=request.form.get("reason", "Customer requested cancellation."),
        status="OPEN",
    )
    db.session.add(ticket)
    log_notification(order.user_id, "Cancellation requested", f"Order #{order.id} has been cancelled and refund flow started.", order=order, channels=["in_app", "email"])
    db.session.commit()
    flash("Order cancelled. Support and refund tracking are now open.", "success")
    return redirect(url_for("main.order_detail", order_id=order.id))


@main_bp.route("/orders/<int:order_id>/reorder", methods=["POST"])
@login_required
def reorder(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session["user_id"]:
        flash("That order is not available for your account.", "danger")
        return redirect(url_for("main.account"))
    new_cart = {}
    for order_item in order.order_items:
        customization = order_item.customization
        new_cart[str(order_item.menu_item_id)] = {
            "quantity": order_item.quantity,
            "spice_level": customization.spice_level if customization else "Medium",
            "removed_ingredients": customization.removed_ingredients if customization else "",
            "selected_addons": split_csv(customization.addon_names if customization else ""),
            "combo_upgrade": customization.combo_upgrade if customization else "Regular",
            "allergy_note": customization.allergy_note if customization else "",
        }
    session["cart"] = new_cart
    session.modified = True
    flash("Previous order added back to your cart.", "success")
    return redirect(url_for("main.cart"))


@main_bp.route("/support/create", methods=["POST"])
@login_required
def create_support_ticket():
    order_id = request.form.get("order_id", type=int)
    ticket = SupportTicket(
        user_id=session["user_id"],
        order_id=order_id,
        subject=request.form["subject"].strip(),
        issue_type=request.form.get("issue_type", "help").strip(),
        message=request.form["message"].strip(),
        status="OPEN",
    )
    db.session.add(ticket)
    db.session.flush()
    db.session.add(SupportMessage(ticket_id=ticket.id, sender_role="user", message=ticket.message))
    db.session.commit()
    flash("Support ticket created.", "success")
    if order_id:
        return redirect(url_for("main.order_detail", order_id=order_id))
    return redirect(url_for("main.account"))


@main_bp.route("/support/<int:ticket_id>/reply", methods=["POST"])
@login_required
def reply_support_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    if ticket.user_id != session["user_id"]:
        flash("That ticket is not available for your account.", "danger")
        return redirect(url_for("main.account"))
    message = request.form.get("message", "").strip()
    if message:
        db.session.add(SupportMessage(ticket_id=ticket.id, sender_role="user", message=message))
        ticket.status = "OPEN"
        db.session.commit()
        flash("Reply sent to support.", "success")
    return redirect(request.referrer or url_for("main.account"))


@main_bp.route("/diet")
def diet():
    goal = request.args.get("goal", "balanced_diet")
    allergy_filter = request.args.get("allergy", "")
    result = build_diet_recommendation(goal, allergy_filter)
    return render_template("diet.html", result=result, selected_goal=goal, selected_allergy=allergy_filter)
