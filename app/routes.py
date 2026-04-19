from datetime import datetime
from functools import wraps

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

from .extensions import db
from .models import Admin, MenuItem, Order, OrderItem, Payment, Restaurant, Review, Staff, User
from .services.location import calculate_distance, fallback_city_coordinates
from .services.overpass import safe_fetch_overpass_restaurants
from .services.recommendations import build_diet_recommendation, history_based_recommendations, menu_item_tags
from .utils.payment import build_upi_payload, fake_transaction_id, generate_qr_data_uri

main_bp = Blueprint("main", __name__)
ORDER_STEPS = ["PLACED", "PREPARING", "OUT_FOR_DELIVERY", "DELIVERED"]


def current_user():
    user_id = session.get("user_id")
    return User.query.get(user_id) if user_id else None


def current_admin():
    admin_id = session.get("admin_id")
    return Admin.query.get(admin_id) if admin_id else None


def current_staff():
    staff_id = session.get("staff_id")
    return Staff.query.get(staff_id) if staff_id else None


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in as admin.", "warning")
            return redirect(url_for("main.admin_login"))
        return view(*args, **kwargs)

    return wrapped_view


def staff_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "staff_id" not in session:
            flash("Please log in as staff.", "warning")
            return redirect(url_for("main.staff_login"))
        return view(*args, **kwargs)

    return wrapped_view


def get_cart():
    return session.setdefault("cart", {})


def cart_context():
    cart = get_cart()
    entries = []
    total = 0
    count = 0

    if not cart:
        return {"entries": [], "total": 0, "count": 0}

    items = MenuItem.query.filter(MenuItem.id.in_(list(map(int, cart.keys())))).all()
    for item in items:
        quantity = cart.get(str(item.id), 0)
        subtotal = item.price * quantity
        total += subtotal
        count += quantity
        entries.append({"menu_item": item, "quantity": quantity, "subtotal": subtotal})

    return {"entries": entries, "total": total, "count": count}


def next_staff_id():
    last_staff = Staff.query.order_by(Staff.id.desc()).first()
    next_number = 1 if not last_staff else int(last_staff.staff_id.replace("STF", "")) + 1
    return f"STF{next_number:03d}"


def create_order_from_cart(user_id):
    cart_data = cart_context()
    order = Order(
        user_id=user_id,
        total_amount=cart_data["total"],
        status="PLACED",
        payment_status="PENDING",
    )
    db.session.add(order)
    db.session.flush()

    for entry in cart_data["entries"]:
        db.session.add(
            OrderItem(
                order_id=order.id,
                menu_item_id=entry["menu_item"].id,
                quantity=entry["quantity"],
                price=entry["menu_item"].price,
            )
        )

    return order, cart_data


def wants_json_response():
    return request.is_json or request.args.get("format") == "json" or request.accept_mimetypes.best == "application/json"


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
        "has_veg": any(item.food_type.lower() == "veg" for item in restaurant.menu_items),
        "has_non_veg": any(item.food_type.lower() == "non-veg" for item in restaurant.menu_items),
        "source": "catalog",
        "url": path,
    }


def serialize_cart_response():
    cart_data = cart_context()
    return {
        "ok": True,
        "count": cart_data["count"],
        "total": round(cart_data["total"], 2),
        "entries": [
            {
                "item_id": entry["menu_item"].id,
                "name": entry["menu_item"].name,
                "price": entry["menu_item"].price,
                "quantity": entry["quantity"],
                "subtotal": round(entry["subtotal"], 2),
                "image_url": entry["menu_item"].image_url,
                "restaurant_name": entry["menu_item"].restaurant.name,
            }
            for entry in cart_data["entries"]
        ],
    }


@main_bp.app_context_processor
def inject_globals():
    return {
        "nav_user": current_user(),
        "nav_admin": current_admin(),
        "nav_staff": current_staff(),
        "cart_meta": cart_context(),
        "menu_item_tags": menu_item_tags,
        "order_steps": ORDER_STEPS,
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
    fallback_city = fallback_city_coordinates("Hyderabad")
    return render_template(
        "index.html",
        restaurants=restaurants,
        recommendations=recommendations,
        top_rated=top_rated,
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
        session.clear()
        session["user_id"] = user.id
        flash("Welcome to FoodSprint.", "success")
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
    return render_template(
        "admin_dashboard.html",
        admin=admin,
        restaurants=restaurants,
        recent_orders=orders,
        total_menu_items=MenuItem.query.count(),
        staff_members=staff_members,
        recent_reviews=recent_reviews,
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


@main_bp.route("/staff/dashboard")
@staff_required
def staff_dashboard():
    staff = current_staff()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("staff_dashboard.html", staff=staff, orders=orders)


@main_bp.route("/staff/update_order/<int:order_id>", methods=["POST"])
@staff_required
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    try:
        current_index = ORDER_STEPS.index(order.status)
    except ValueError:
        current_index = 0
    if current_index < len(ORDER_STEPS) - 1:
        order.status = ORDER_STEPS[current_index + 1]
        db.session.commit()
        flash(f"Order #{order.id} updated to {order.status.replace('_', ' ')}.", "success")
    else:
        flash("This order is already delivered.", "info")
    return redirect(url_for("main.staff_dashboard"))


@main_bp.route("/restaurants/<int:restaurant_id>")
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant.id).all()
    recommended_items = menu_items[:4]
    reviews = Review.query.filter_by(restaurant_id=restaurant.id).order_by(Review.created_at.desc()).all()
    cart_quantities = session.get("cart", {})
    return render_template(
        "restaurant_detail.html",
        restaurant=restaurant,
        menu_items=menu_items,
        recommended_items=recommended_items,
        also_ordered=[],
        reviews=reviews,
        cart_quantities=cart_quantities,
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
    item_id = request.form.get("item_id") or (request.get_json(silent=True) or {}).get("item_id")
    quantity = int(request.form.get("quantity", 1) or (request.get_json(silent=True) or {}).get("quantity", 1))
    if not item_id:
        return redirect(url_for("main.cart"))
    MenuItem.query.get_or_404(item_id)
    cart = get_cart()
    cart[str(item_id)] = cart.get(str(item_id), 0) + quantity
    session.modified = True
    if request.is_json:
        return jsonify(serialize_cart_response())
    flash("Item added to cart.", "success")
    return redirect(request.referrer or url_for("main.cart"))


@main_bp.route("/cart/update", methods=["POST"])
def update_cart():
    item_id = request.form.get("item_id") or (request.get_json(silent=True) or {}).get("item_id")
    quantity = int(request.form.get("quantity", 0) or (request.get_json(silent=True) or {}).get("quantity", 0))
    cart = get_cart()
    if quantity <= 0:
        cart.pop(str(item_id), None)
    else:
        cart[str(item_id)] = quantity
    session.modified = True
    if request.is_json:
        return jsonify(serialize_cart_response())
    return redirect(url_for("main.cart"))


@main_bp.route("/checkout")
@login_required
def checkout():
    admin = Admin.query.first()
    return render_template("checkout.html", cart_data=cart_context(), admin_upi_id=admin.upi_id if admin else "")


@main_bp.route("/payment/upi", methods=["POST"])
@login_required
def payment_upi():
    admin = Admin.query.first()
    if not admin or not admin.upi_id:
        flash("Admin UPI ID is not configured yet.", "danger")
        return redirect(url_for("main.checkout"))

    if cart_context()["count"] == 0:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("main.cart"))

    order, cart_data = create_order_from_cart(session["user_id"])
    payload = build_upi_payload(admin.upi_id, cart_data["total"])
    qr_code = generate_qr_data_uri(payload)

    payment = Payment(
        order_id=order.id,
        method="UPI",
        status="PENDING",
        upi_id=admin.upi_id,
        qr_payload=payload,
    )
    db.session.add(payment)
    db.session.commit()

    return render_template(
        "payment.html",
        qr_code=qr_code,
        upi_id=admin.upi_id,
        amount=cart_data["total"],
        order_id=order.id,
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
    return render_template("order_tracking.html", order=order)


@main_bp.route("/diet")
def diet():
    goal = request.args.get("goal", "balanced_diet")
    result = build_diet_recommendation(goal)
    return render_template("diet.html", result=result, selected_goal=goal)
