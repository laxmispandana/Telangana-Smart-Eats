from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    orders = db.relationship("Order", backref="user", lazy=True)
    reviews = db.relationship("Review", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False, index=True)
    area = db.Column(db.String(120), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    cuisine = db.Column(db.String(120), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    delivery_time = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    menu_items = db.relationship("MenuItem", backref="restaurant", lazy=True)
    reviews = db.relationship("Review", backref="restaurant", lazy=True)


class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(
        db.Integer, db.ForeignKey("restaurant.id"), nullable=False, index=True
    )
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    food_type = db.Column(db.String(20), nullable=False)
    calories = db.Column(db.Integer, nullable=True)
    healthy_badge = db.Column(db.Boolean, default=False, nullable=False)
    review_items = db.relationship("Review", backref="menu_item", lazy=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(50), nullable=False, default="pending")
    payment_reference = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Placed")
    order_items = db.relationship("OrderItem", backref="order", lazy=True)
    payments = db.relationship(
        "PaymentTransaction",
        backref="order",
        lazy=True,
        order_by="desc(PaymentTransaction.created_at)",
    )
    status_events = db.relationship(
        "OrderStatusEvent",
        backref="order",
        lazy=True,
        order_by="OrderStatusEvent.created_at.asc()",
    )

    @property
    def latest_payment(self):
        return self.payments[0] if self.payments else None


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False, index=True)
    menu_item_id = db.Column(
        db.Integer, db.ForeignKey("menu_item.id"), nullable=False, index=True
    )
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)
    menu_item = db.relationship("MenuItem")


class PaymentTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False, index=True)
    provider = db.Column(db.String(40), nullable=False, default="manual")
    method = db.Column(db.String(40), nullable=False, default="UPI")
    status = db.Column(db.String(40), nullable=False, default="pending")
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(120), nullable=True, index=True)
    gateway_order_id = db.Column(db.String(120), nullable=True, index=True)
    gateway_payment_id = db.Column(db.String(120), nullable=True, index=True)
    gateway_signature = db.Column(db.String(255), nullable=True)
    upi_id = db.Column(db.String(120), nullable=True)
    qr_payload = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class OrderStatusEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    restaurant_id = db.Column(
        db.Integer, db.ForeignKey("restaurant.id"), nullable=False, index=True
    )
    menu_item_id = db.Column(
        db.Integer, db.ForeignKey("menu_item.id"), nullable=True, index=True
    )
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
