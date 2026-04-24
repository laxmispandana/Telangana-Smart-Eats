from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    orders = db.relationship("Order", backref="user", lazy=True)
    reviews = db.relationship("Review", backref="user", lazy=True)
    addresses = db.relationship("Address", backref="user", lazy=True, order_by="Address.is_default.desc(), Address.id.asc()")
    favorites = db.relationship("Favorite", backref="user", lazy=True)
    loyalty_entries = db.relationship("LoyaltyEntry", backref="user", lazy=True)
    notifications = db.relationship("NotificationLog", backref="user", lazy=True)
    support_tickets = db.relationship("SupportTicket", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Admin(db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    upi_id = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Restaurant(db.Model):
    __tablename__ = "restaurant"

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
    favorites = db.relationship("Favorite", backref="restaurant", lazy=True)


class RestaurantProfile(db.Model):
    __tablename__ = "restaurant_profile"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False, unique=True, index=True)
    delivery_fee = db.Column(db.Float, nullable=False, default=35)
    min_order_amount = db.Column(db.Float, nullable=False, default=149)
    opening_time = db.Column(db.String(5), nullable=False, default="09:00")
    closing_time = db.Column(db.String(5), nullable=False, default="23:00")
    pickup_enabled = db.Column(db.Boolean, nullable=False, default=True)
    offers_text = db.Column(db.String(255), nullable=True)
    support_phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    restaurant = db.relationship("Restaurant", backref=db.backref("profile", uselist=False))


class MenuItem(db.Model):
    __tablename__ = "menu_item"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    food_type = db.Column(db.String(20), nullable=False)
    calories = db.Column(db.Integer, nullable=True)
    healthy_badge = db.Column(db.Boolean, default=False, nullable=False)


class MenuNutrition(db.Model):
    __tablename__ = "menu_nutrition"

    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_item.id"), nullable=False, unique=True, index=True)
    protein_g = db.Column(db.Integer, nullable=False, default=12)
    carbs_g = db.Column(db.Integer, nullable=False, default=30)
    fat_g = db.Column(db.Integer, nullable=False, default=10)
    allergens = db.Column(db.String(255), nullable=True)
    diet_labels = db.Column(db.String(255), nullable=True)

    menu_item = db.relationship("MenuItem", backref=db.backref("nutrition", uselist=False))


class MenuOption(db.Model):
    __tablename__ = "menu_option"

    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_item.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    option_type = db.Column(db.String(50), nullable=False, default="addon")
    choices = db.Column(db.Text, nullable=False)
    price_delta_map = db.Column(db.Text, nullable=True)

    menu_item = db.relationship("MenuItem", backref="options")


class MenuAvailability(db.Model):
    __tablename__ = "menu_availability"

    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_item.id"), nullable=False, unique=True, index=True)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    stock_count = db.Column(db.Integer, nullable=False, default=25)

    menu_item = db.relationship("MenuItem", backref=db.backref("availability", uselist=False))


class Address(db.Model):
    __tablename__ = "address"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    label = db.Column(db.String(50), nullable=False, default="Home")
    recipient_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line = db.Column(db.String(255), nullable=False)
    landmark = db.Column(db.String(120), nullable=True)
    city = db.Column(db.String(120), nullable=False)
    delivery_notes = db.Column(db.String(255), nullable=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Favorite(db.Model):
    __tablename__ = "favorite"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class PromoCode(db.Model):
    __tablename__ = "promo_code"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=False)
    discount_type = db.Column(db.String(20), nullable=False, default="flat")
    discount_value = db.Column(db.Float, nullable=False, default=0)
    min_order_amount = db.Column(db.Float, nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)
    first_order_only = db.Column(db.Boolean, nullable=False, default=False)
    free_delivery = db.Column(db.Boolean, nullable=False, default=False)


class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="PLACED")
    payment_status = db.Column(db.String(50), nullable=False, default="PENDING")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    order_items = db.relationship("OrderItem", backref="order", lazy=True)
    payments = db.relationship(
        "Payment",
        backref="order",
        lazy=True,
        order_by="Payment.created_at.asc()",
    )
    support_tickets = db.relationship("SupportTicket", backref="order", lazy=True)
    notifications = db.relationship("NotificationLog", backref="order", lazy=True)

    @property
    def latest_payment(self):
        return self.payments[-1] if self.payments else None


class OrderItem(db.Model):
    __tablename__ = "order_item"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False, index=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_item.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)

    menu_item = db.relationship("MenuItem")


class OrderItemCustomization(db.Model):
    __tablename__ = "order_item_customization"

    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey("order_item.id"), nullable=False, unique=True, index=True)
    spice_level = db.Column(db.String(20), nullable=True)
    removed_ingredients = db.Column(db.String(255), nullable=True)
    addon_names = db.Column(db.String(255), nullable=True)
    combo_upgrade = db.Column(db.String(120), nullable=True)
    allergy_note = db.Column(db.String(255), nullable=True)

    order_item = db.relationship("OrderItem", backref=db.backref("customization", uselist=False))


class OrderFulfillment(db.Model):
    __tablename__ = "order_fulfillment"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False, unique=True, index=True)
    fulfillment_mode = db.Column(db.String(20), nullable=False, default="delivery")
    scheduled_for = db.Column(db.DateTime, nullable=True)
    address_snapshot = db.Column(db.Text, nullable=True)
    delivery_notes = db.Column(db.String(255), nullable=True)
    special_instructions = db.Column(db.String(255), nullable=True)
    eta_minutes = db.Column(db.Integer, nullable=False, default=30)
    rider_name = db.Column(db.String(120), nullable=True)
    rider_phone = db.Column(db.String(20), nullable=True)
    split_count = db.Column(db.Integer, nullable=False, default=1)
    split_amount = db.Column(db.Float, nullable=False, default=0)
    promo_code = db.Column(db.String(40), nullable=True)
    discount_amount = db.Column(db.Float, nullable=False, default=0)
    delivery_fee = db.Column(db.Float, nullable=False, default=0)
    loyalty_points_used = db.Column(db.Integer, nullable=False, default=0)
    loyalty_points_earned = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    order = db.relationship("Order", backref=db.backref("fulfillment", uselist=False))


class Payment(db.Model):
    __tablename__ = "payment"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False, index=True)
    method = db.Column(db.String(40), nullable=False, default="UPI")
    status = db.Column(db.String(50), nullable=False, default="PENDING")
    transaction_id = db.Column(db.String(120), nullable=True)
    upi_id = db.Column(db.String(120), nullable=True)
    qr_payload = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class LoyaltyEntry(db.Model):
    __tablename__ = "loyalty_entry"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=True, index=True)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class UserReferral(db.Model):
    __tablename__ = "user_referral"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True, index=True)
    referral_code = db.Column(db.String(40), nullable=False, unique=True, index=True)
    referred_by_code = db.Column(db.String(40), nullable=True)
    referral_rewarded = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", backref=db.backref("referral", uselist=False))


class NotificationLog(db.Model):
    __tablename__ = "notification_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=True, index=True)
    channel = db.Column(db.String(30), nullable=False, default="in_app")
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class SupportTicket(db.Model):
    __tablename__ = "support_ticket"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=True, index=True)
    subject = db.Column(db.String(120), nullable=False)
    issue_type = db.Column(db.String(50), nullable=False, default="help")
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="OPEN")
    resolution_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    messages = db.relationship("SupportMessage", backref="ticket", lazy=True, order_by="SupportMessage.created_at.asc()")


class SupportMessage(db.Model):
    __tablename__ = "support_message"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("support_ticket.id"), nullable=False, index=True)
    sender_role = db.Column(db.String(20), nullable=False, default="user")
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Review(db.Model):
    __tablename__ = "review"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ReviewPhoto(db.Model):
    __tablename__ = "review_photo"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("review.id"), nullable=False, unique=True, index=True)
    image_url = db.Column(db.String(255), nullable=False)

    review = db.relationship("Review", backref=db.backref("photo", uselist=False))
