import re
import uuid
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
from .models import (
    Admin,
    MenuItem,
    Order,
    PaymentTransaction,
    Restaurant,
    Review,
    User,
)
from .services.cache_store import cache_store
from .services.location import normalize_telangana_city, resolve_telangana_city
from .services.notifications import emit_cart_update, emit_order_update, emit_toast
from .services.orders import (
    ORDER_STATUS_FLOW,
    PAYMENT_STATUS_FLOW,
    append_order_status,
    create_order_with_items,
    create_payment_record,
    serialize_order_timeline,
)
from .services.payments import (
    build_upi_app_links,
    build_upi_uri,
    create_razorpay_order,
    generate_qr_code_data_uri,
    manual_upi_configured,
    razorpay_configured,
    verify_razorpay_signature,
)
from .services.recommendations import (
    build_diet_recommendation,
    haversine_distance,
    history_based_recommendations,
    is_popular_item,
    menu_item_tags,
    people_also_ordered,
)

main_bp = Blueprint("main", __name__)

UPI_ID_PATTERN = re.compile(r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$")


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_user():
    user_id = session.get("user_id")
    return User.query.get(user_id) if user_id else None


def admin_logged_in():
    return session.get("admin_id") is not None


def current_admin():
    admin_id = session.get("admin_id")
    return Admin.query.get(admin_id) if admin_id else None


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not admin_logged_in():
            flash("Please log in as admin to continue.", "warning")
            return redirect(url_for("main.admin_login"))
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
        return {"entries": entries, "total": total, "count": count}

    menu_items = MenuItem.query.filter(MenuItem.id.in_(list(map(int, cart.keys())))).all()
    menu_map = {item.id: item for item in menu_items}

    for item_id, quantity in cart.items():
        menu_item = menu_map.get(int(item_id))
        if not menu_item:
            continue
        subtotal = menu_item.price * quantity
        total += subtotal
        count += quantity
        entries.append({"menu_item": menu_item, "quantity": quantity, "subtotal": subtotal})

    return {"entries": entries, "total": total, "count": count}


def get_fallback_city():
    user = current_user()
    return normalize_telangana_city(user.location if user else None) or "Hyderabad"


def validate_upi_id(upi_id):
    return bool(upi_id and UPI_ID_PATTERN.match(upi_id.strip()))


def get_order_or_404_for_user(order_id):
    order = Order.query.get_or_404(order_id)
    if not admin_logged_in() and order.user_id != session.get("user_id"):
        return None
    return order


def latest_payment_or_placeholder(order):
    if order.latest_payment:
        return order.latest_payment
    payment = PaymentTransaction(
        order_id=order.id,
        provider="system",
        method="Unknown",
        status=order.payment_status,
        amount=order.total_amount,
    )
    db.session.add(payment)
    return payment


def emit_order_event(order, message):
    emit_order_update(order, message=message)
    emit_toast(f"user:{order.user_id}", "Order update", message, level="success")


@main_bp.app_context_processor
def inject_globals():
    return {
        "nav_user": current_user(),
        "cart_meta": cart_context(),
        "admin_logged_in": admin_logged_in(),
        "nav_admin": current_admin(),
        "menu_item_tags": menu_item_tags,
        "is_popular_item": is_popular_item,
        "order_status_flow": ORDER_STATUS_FLOW,
    }


@main_bp.route("/")
def index():
    restaurants = Restaurant.query.order_by(Restaurant.rating.desc()).all()
    top_rated = Restaurant.query.order_by(Restaurant.rating.desc()).limit(3).all()
    recommendations = (
        history_based_recommendations(session["user_id"])
        if "user_id" in session
        else MenuItem.query.filter_by(healthy_badge=True).limit(6).all()
    )
    return render_template(
        "index.html",
        restaurants=restaurants,
        top_rated=top_rated,
        recommendations=recommendations,
        fallback_city=get_fallback_city(),
    )


@main_bp.route("/location/context")
def location_context():
    fallback_city = normalize_telangana_city(request.args.get("fallback_city")) or get_fallback_city()
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    if lat is None or lng is None:
        return jsonify({"ok": True, "mode": "fallback", "city": fallback_city})

    cache_key = f"location:{round(lat, 3)}:{round(lng, 3)}"
    cached = cache_store.get_json(cache_key)
    if cached:
        return jsonify({"ok": True, "mode": "precise", **cached})

    resolved = resolve_telangana_city(lat, lng)
    cache_store.set_json(cache_key, resolved, ttl=600)
    return jsonify({"ok": True, "mode": "precise", **resolved})


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
        session["user_id"] = user.id
        flash("Welcome aboard. Your account is ready.", "success")
        return redirect(url_for("main.index"))

    return render_template("signup.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(request.form["password"]):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("main.login"))

        session["user_id"] = user.id
        flash("Welcome back.", "success")
        return redirect(url_for("main.index"))

    return render_template("login.html")


@main_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@main_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        admin = Admin.query.filter_by(email=email).first()
        if not admin and email == current_app.config["ADMIN_EMAIL"].strip().lower():
            seeded_admin = Admin(
                name="Platform Admin",
                email=current_app.config["ADMIN_EMAIL"].strip().lower(),
            )
            seeded_admin.set_password(current_app.config["ADMIN_PASSWORD"])
            db.session.add(seeded_admin)
            db.session.commit()
            admin = seeded_admin

        if admin and admin.check_password(password):
            session["admin_id"] = admin.id
            flash("Admin access granted.", "success")
            return redirect(url_for("main.admin_dashboard"))

        flash("Invalid admin credentials.", "danger")
        return redirect(url_for("main.admin_login"))

    return render_template("admin_login.html")


@main_bp.route("/admin/register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        if Admin.query.filter_by(email=email).first():
            flash("An admin account with that email already exists.", "danger")
            return redirect(url_for("main.admin_register"))

        admin = Admin(name=request.form["name"].strip(), email=email)
        admin.set_password(request.form["password"])
        db.session.add(admin)
        db.session.commit()
        session["admin_id"] = admin.id
        flash("Admin account created successfully.", "success")
        return redirect(url_for("main.admin_dashboard"))

    return render_template("admin_register.html")


@main_bp.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    flash("Admin session closed.", "info")
    return redirect(url_for("main.index"))


@main_bp.route("/admin")
@admin_required
def admin_dashboard():
    restaurants = Restaurant.query.order_by(Restaurant.name.asc()).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(20).all()
    total_menu_items = MenuItem.query.count()
    recent_reviews = Review.query.order_by(Review.created_at.desc()).limit(10).all()
    return render_template(
        "admin_dashboard.html",
        restaurants=restaurants,
        recent_orders=recent_orders,
        total_menu_items=total_menu_items,
        recent_reviews=recent_reviews,
    )


@main_bp.route("/admin/restaurants/new", methods=["POST"])
@admin_required
def admin_create_restaurant():
    restaurant = Restaurant(
        name=request.form["name"].strip(),
        city=request.form["city"].strip(),
        area=request.form["area"].strip(),
        lat=float(request.form["lat"]),
        lng=float(request.form["lng"]),
        rating=float(request.form["rating"]),
        category=request.form["category"].strip(),
        cuisine=request.form["cuisine"].strip(),
        image_url=request.form["image_url"].strip(),
        delivery_time=int(request.form["delivery_time"]),
        description=request.form["description"].strip(),
    )
    db.session.add(restaurant)
    db.session.commit()
    cache_store.delete("restaurants-feed")
    flash("Restaurant added successfully.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/menu/new", methods=["POST"])
@admin_required
def admin_create_menu_item():
    item = MenuItem(
        restaurant_id=int(request.form["restaurant_id"]),
        name=request.form["name"].strip(),
        description=request.form["description"].strip(),
        price=float(request.form["price"]),
        image_url=request.form["image_url"].strip(),
        category=request.form["category"].strip(),
        food_type=request.form["food_type"].strip(),
        calories=int(request.form["calories"]) if request.form.get("calories") else None,
        healthy_badge=bool(request.form.get("healthy_badge")),
    )
    db.session.add(item)
    db.session.commit()
    flash("Menu item added successfully.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    next_status = request.form.get("status", "").strip()
    next_payment_status = request.form.get("payment_status", "").strip() or order.payment_status
    if next_status and next_status not in ORDER_STATUS_FLOW:
        flash("Invalid order status.", "danger")
        return redirect(url_for("main.admin_dashboard"))
    if next_payment_status not in PAYMENT_STATUS_FLOW:
        flash("Invalid payment status.", "danger")
        return redirect(url_for("main.admin_dashboard"))

    if next_status and next_status != order.status:
        append_order_status(order, next_status, note="Updated by admin")
    order.payment_status = next_payment_status
    payment = latest_payment_or_placeholder(order)
    payment.status = next_payment_status
    db.session.commit()
    emit_order_event(order, f"Order #{order.id} is now {order.status}.")
    flash("Order updated successfully.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/restaurants/<int:restaurant_id>")
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    related = MenuItem.query.filter_by(restaurant_id=restaurant.id).all()
    reviews = (
        Review.query.filter_by(restaurant_id=restaurant.id)
        .order_by(Review.created_at.desc())
        .limit(10)
        .all()
    )
    recommended_items = sorted(
        related,
        key=lambda item: (
            "Popular 🔥" not in menu_item_tags(item),
            "Healthy 🥗" not in menu_item_tags(item),
            item.price,
        ),
    )[:4]
    also_ordered = people_also_ordered({item.id for item in related}, limit=4)
    return render_template(
        "restaurant_detail.html",
        restaurant=restaurant,
        menu_items=related,
        reviews=reviews,
        recommended_items=recommended_items,
        also_ordered=also_ordered,
        cart_quantities=session.get("cart", {}),
    )


@main_bp.route("/restaurants/<int:restaurant_id>/reviews", methods=["POST"])
@login_required
def add_review(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    menu_item_id = request.form.get("menu_item_id", type=int)
    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment", "").strip()

    if rating is None or rating < 1 or rating > 5 or not comment:
        flash("Please submit a rating between 1 and 5 and write a review comment.", "danger")
        return redirect(url_for("main.restaurant_detail", restaurant_id=restaurant.id))

    review = Review(
        user_id=session["user_id"],
        restaurant_id=restaurant.id,
        menu_item_id=menu_item_id if menu_item_id else None,
        rating=rating,
        comment=comment,
    )
    db.session.add(review)
    db.session.commit()
    flash("Thanks for sharing your review.", "success")
    return redirect(url_for("main.restaurant_detail", restaurant_id=restaurant.id))


@main_bp.route("/cart")
def cart():
    return render_template("cart.html", cart_data=cart_context())


@main_bp.route("/cart/add", methods=["POST"])
def add_to_cart():
    payload = request.get_json(silent=True) or {}
    item_id = request.form.get("item_id") or payload.get("item_id")
    quantity = int(request.form.get("quantity", 1) or payload.get("quantity", 1))
    MenuItem.query.get_or_404(item_id)
    cart = get_cart()
    cart[str(item_id)] = cart.get(str(item_id), 0) + quantity
    session.modified = True
    meta = cart_context()
    if session.get("user_id"):
        emit_cart_update(session["user_id"], meta)

    if request.is_json:
        return jsonify({"ok": True, "count": meta["count"], "total": meta["total"]})

    flash("Item added to cart.", "success")
    return redirect(request.referrer or url_for("main.cart"))


@main_bp.route("/cart/update", methods=["POST"])
def update_cart():
    payload = request.get_json(silent=True) or {}
    item_id = str(request.form.get("item_id") or payload.get("item_id"))
    quantity = int(request.form.get("quantity") or payload.get("quantity", 1))
    cart = get_cart()
    if quantity <= 0:
        cart.pop(item_id, None)
    else:
        cart[item_id] = quantity
    session.modified = True
    meta = cart_context()
    if session.get("user_id"):
        emit_cart_update(session["user_id"], meta)

    if request.is_json:
        return jsonify({"ok": True, "count": meta["count"], "total": meta["total"]})

    return redirect(url_for("main.cart"))


@main_bp.route("/restaurants/data")
def restaurants_data():
    user_lat = request.args.get("lat", type=float)
    user_lng = request.args.get("lng", type=float)
    radius = request.args.get("radius", type=float, default=10)
    search = request.args.get("search", "").strip().lower()
    food_type = request.args.get("food_type", "").strip().lower()
    healthy = request.args.get("healthy", "").strip().lower() == "true"
    min_rating = request.args.get("rating", type=float, default=0)
    city_hint = normalize_telangana_city(request.args.get("city")) or get_fallback_city()
    page = max(request.args.get("page", type=int, default=1), 1)
    per_page = min(max(request.args.get("per_page", type=int, default=12), 1), 30)

    cache_key = f"restaurants:{user_lat}:{user_lng}:{radius}:{search}:{food_type}:{healthy}:{min_rating}:{city_hint}"
    cached = cache_store.get_json(cache_key)
    if cached:
        payload = cached
    else:
        restaurants = Restaurant.query.all()
        payload = []
        for restaurant in restaurants:
            if search and search not in restaurant.name.lower() and search not in restaurant.city.lower():
                continue
            if food_type and restaurant.category != food_type:
                continue
            if restaurant.rating < min_rating:
                continue
            if healthy and restaurant.category not in {"diet", "veg"}:
                continue

            distance = None
            if user_lat is not None and user_lng is not None:
                distance = haversine_distance(user_lat, user_lng, restaurant.lat, restaurant.lng)
                if radius and distance > radius:
                    continue

            payload.append(
                {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "city": restaurant.city,
                    "area": restaurant.area,
                    "rating": restaurant.rating,
                    "category": restaurant.category,
                    "cuisine": restaurant.cuisine,
                    "image_url": restaurant.image_url,
                    "distance": round(distance, 1) if distance is not None else None,
                    "lat": restaurant.lat,
                    "lng": restaurant.lng,
                    "delivery_time": restaurant.delivery_time,
                    "description": restaurant.description,
                    "popular": restaurant.rating >= 4.6,
                    "city_match": restaurant.city.lower() == city_hint.lower(),
                }
            )

        if user_lat is not None and user_lng is not None:
            payload.sort(
                key=lambda item: (item["distance"] is None, item["distance"] or 9999, -item["rating"])
            )
        else:
            payload.sort(key=lambda item: (not item["city_match"], -item["rating"], item["delivery_time"]))
        cache_store.set_json(cache_key, payload, ttl=120)

    total = len(payload)
    start = (page - 1) * per_page
    end = start + per_page
    response = jsonify(payload[start:end])
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Total-Pages"] = str(max(1, (total + per_page - 1) // per_page))
    return response


@main_bp.route("/diet", methods=["GET", "POST"])
def diet():
    goal = request.values.get("goal", "balanced_diet")
    result = build_diet_recommendation(goal)
    return render_template("diet.html", result=result, selected_goal=goal)


@main_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    meta = cart_context()
    if meta["count"] == 0:
        flash("Add items to your cart before checkout.", "warning")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        order = create_order_with_items(
            session["user_id"],
            meta,
            status="Placed",
            payment_status="paid",
        )
        order.payment_reference = f"DEMO-{uuid.uuid4().hex[:10].upper()}"
        create_payment_record(
            order,
            provider="demo",
            method="Demo",
            amount=meta["total"],
            status="paid",
            transaction_id=order.payment_reference,
        )
        db.session.commit()
        session["cart"] = {}
        emit_order_event(order, f"Order #{order.id} has been placed successfully.")
        flash("Demo payment completed successfully.", "success")
        return redirect(url_for("main.order_confirmation", order_id=order.id))

    return render_template(
        "checkout.html",
        cart_data=meta,
        razorpay_enabled=razorpay_configured(),
        manual_upi_enabled=manual_upi_configured(),
        razorpay_key_id=current_app.config["RAZORPAY_KEY_ID"],
        payee_upi_id=current_app.config["FOODSPRINT_UPI_ID"],
        payee_upi_name=current_app.config["FOODSPRINT_UPI_NAME"],
    )


@main_bp.route("/payments/razorpay/order", methods=["POST"])
@login_required
def create_razorpay_checkout_order():
    meta = cart_context()
    payload = request.get_json(silent=True) or {}
    preferred_method = payload.get("preferred_method", "UPI/Card")
    if meta["count"] == 0:
        return jsonify({"ok": False, "message": "Cart is empty."}), 400
    if not razorpay_configured():
        return jsonify({"ok": False, "message": "Razorpay is not configured."}), 400

    try:
        order = create_order_with_items(session["user_id"], meta, status="Placed", payment_status="pending")
        gateway_order = create_razorpay_order(order)
        order.payment_reference = gateway_order["id"]
        create_payment_record(
            order,
            provider="razorpay",
            method=preferred_method,
            amount=meta["total"],
            status="pending",
            gateway_order_id=gateway_order["id"],
            metadata_json={"currency": gateway_order["currency"]},
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"ok": False, "message": "Unable to initialize Razorpay order."}), 502

    emit_order_event(order, f"Order #{order.id} is waiting for payment confirmation.")
    return jsonify(
        {
            "ok": True,
            "internal_order_id": order.id,
            "razorpay_order_id": gateway_order["id"],
            "amount": gateway_order["amount"],
            "currency": gateway_order["currency"],
            "key": current_app.config["RAZORPAY_KEY_ID"],
            "name": "FoodSprint",
            "description": "Telangana smart food ordering",
            "prefill": {
                "name": current_user().name,
                "email": current_user().email,
                "contact": current_user().phone,
            },
        }
    )


@main_bp.route("/payments/razorpay/verify", methods=["POST"])
@login_required
def verify_razorpay_payment():
    payload = request.get_json(silent=True) or {}
    order = Order.query.get_or_404(payload.get("internal_order_id"))
    if order.user_id != session["user_id"]:
        return jsonify({"ok": False, "message": "Unauthorized order access."}), 403

    signature_ok = verify_razorpay_signature(
        payload.get("razorpay_order_id", ""),
        payload.get("razorpay_payment_id", ""),
        payload.get("razorpay_signature", ""),
    )
    payment = order.latest_payment or latest_payment_or_placeholder(order)
    if not signature_ok:
        order.payment_status = "failed"
        payment.status = "failed"
        payment.gateway_payment_id = payload.get("razorpay_payment_id")
        payment.gateway_signature = payload.get("razorpay_signature")
        db.session.commit()
        emit_order_event(order, f"Payment failed for order #{order.id}.")
        return jsonify({"ok": False, "message": "Signature verification failed."}), 400

    order.payment_status = "paid"
    order.payment_reference = payload.get("razorpay_payment_id")
    payment.status = "paid"
    payment.gateway_payment_id = payload.get("razorpay_payment_id")
    payment.gateway_signature = payload.get("razorpay_signature")
    db.session.commit()
    session["cart"] = {}
    emit_order_event(order, f"Payment received for order #{order.id}.")
    return jsonify({"ok": True, "redirect_url": url_for("main.order_confirmation", order_id=order.id)})


@main_bp.route("/payments/upi/create", methods=["POST"])
@login_required
def create_manual_upi_payment():
    if not manual_upi_configured():
        return jsonify({"ok": False, "message": "Manual UPI is not configured."}), 400

    meta = cart_context()
    payload = request.get_json(silent=True) or {}
    payer_upi_id = payload.get("upi_id", "").strip()
    if meta["count"] == 0:
        return jsonify({"ok": False, "message": "Cart is empty."}), 400
    if payer_upi_id and not validate_upi_id(payer_upi_id):
        return jsonify({"ok": False, "message": "Please enter a valid UPI ID."}), 400

    order = create_order_with_items(session["user_id"], meta, status="Placed", payment_status="pending")
    upi_uri = build_upi_uri(order.id, meta["total"])
    qr_data_uri = generate_qr_code_data_uri(upi_uri)
    payment = create_payment_record(
        order,
        provider="manual_upi",
        method="UPI",
        amount=meta["total"],
        status="pending",
        upi_id=payer_upi_id or None,
        qr_payload=upi_uri,
        metadata_json={"intent_links": build_upi_app_links(upi_uri)},
    )
    db.session.commit()
    emit_order_event(order, f"Manual UPI instructions generated for order #{order.id}.")
    return jsonify(
        {
            "ok": True,
            "order_id": order.id,
            "amount": meta["total"],
            "qr_code": qr_data_uri,
            "upi_uri": upi_uri,
            "intent_links": payment.metadata_json["intent_links"],
            "redirect_url": url_for("main.track_order", order_id=order.id),
        }
    )


@main_bp.route("/payments/upi/confirm", methods=["POST"])
@login_required
def confirm_manual_upi_payment():
    payload = request.get_json(silent=True) or {}
    order = Order.query.get_or_404(payload.get("order_id"))
    if order.user_id != session["user_id"]:
        return jsonify({"ok": False, "message": "Unauthorized order access."}), 403

    transaction_id = (payload.get("transaction_id") or "").strip()
    upi_id = (payload.get("upi_id") or "").strip()
    if not transaction_id:
        return jsonify({"ok": False, "message": "Enter the UPI transaction ID to continue."}), 400
    if upi_id and not validate_upi_id(upi_id):
        return jsonify({"ok": False, "message": "Please enter a valid UPI ID."}), 400

    payment = order.latest_payment or latest_payment_or_placeholder(order)
    payment.status = "verification_pending"
    payment.transaction_id = transaction_id
    payment.upi_id = upi_id or payment.upi_id
    order.payment_status = "verification_pending"
    db.session.commit()
    emit_order_event(order, f"UPI proof submitted for order #{order.id}. Awaiting verification.")
    emit_toast("admins", "UPI verification", f"Order #{order.id} needs manual UPI verification.", level="info")
    return jsonify({"ok": True, "redirect_url": url_for("main.track_order", order_id=order.id)})


@main_bp.route("/payment/failure")
@login_required
def payment_failure():
    order = None
    order_id = request.args.get("order_id", type=int)
    if order_id:
        order = Order.query.get(order_id)
        if order and order.user_id == session["user_id"]:
            order.payment_status = "failed"
            payment = order.latest_payment or latest_payment_or_placeholder(order)
            payment.status = "failed"
            db.session.commit()
            emit_order_event(order, f"Payment failed for order #{order.id}.")
    return render_template("payment_failure.html", order=order)


@main_bp.route("/orders/<int:order_id>/confirmation")
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session["user_id"]:
        flash("That order is not available for your account.", "danger")
        return redirect(url_for("main.index"))
    recommendations = history_based_recommendations(session["user_id"])
    return render_template(
        "order_confirmation.html",
        order=order,
        recommendations=recommendations,
        timeline=serialize_order_timeline(order),
    )


@main_bp.route("/orders/<int:order_id>/track")
@login_required
def track_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session["user_id"]:
        flash("That order is not available for your account.", "danger")
        return redirect(url_for("main.index"))
    return render_template(
        "order_tracking.html",
        order=order,
        timeline=serialize_order_timeline(order),
    )


@main_bp.route("/orders/<int:order_id>/status")
@login_required
def order_status_api(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session["user_id"]:
        return jsonify({"ok": False, "message": "Unauthorized order access."}), 403
    payment = order.latest_payment
    return jsonify(
        {
            "ok": True,
            "order_id": order.id,
            "status": order.status,
            "payment_status": order.payment_status,
            "payment_method": payment.method if payment else "Unknown",
            "timeline": serialize_order_timeline(order),
        }
    )
