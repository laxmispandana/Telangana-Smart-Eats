import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from .extensions import db, migrate, socketio
from .routes import main_bp
from .services.cache_store import cache_store
from .services.data_seed import seed_data


def configure_logging(app):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    app.logger.setLevel(logging.INFO)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api") or request.is_json:
            return jsonify({"ok": False, "message": "Resource not found."}), 404
        return render_template("error.html", title="Page not found", message="The page you requested could not be found."), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception("Unhandled application error: %s", error)
        if request.path.startswith("/api") or request.is_json:
            return jsonify({"ok": False, "message": "Something went wrong on our side."}), 500
        return render_template("error.html", title="Server error", message="Something went wrong. Please try again."), 500


def create_app():
    load_dotenv()
    app = Flask(__name__)
    database_url = os.getenv("DATABASE_URL", "sqlite:///food_ordering.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SPOONACULAR_API_KEY"] = os.getenv("SPOONACULAR_API_KEY", "")
    app.config["RAZORPAY_KEY_ID"] = os.getenv("RAZORPAY_KEY_ID", "")
    app.config["RAZORPAY_KEY_SECRET"] = os.getenv("RAZORPAY_KEY_SECRET", "")
    app.config["APP_BASE_URL"] = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")
    app.config["ADMIN_EMAIL"] = os.getenv("ADMIN_EMAIL", "admin@foodsprint.local")
    app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "admin123")
    app.config["REDIS_URL"] = os.getenv("REDIS_URL", "")
    app.config["FOODSPRINT_UPI_ID"] = os.getenv("FOODSPRINT_UPI_ID", "foodsprint@upi")
    app.config["FOODSPRINT_UPI_NAME"] = os.getenv("FOODSPRINT_UPI_NAME", "FoodSprint")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"

    configure_logging(app)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    cache_store.init_app(app)

    with app.app_context():
        from . import models  # noqa: F401
        from . import realtime  # noqa: F401

        db.create_all()
        seed_data()

    app.register_blueprint(main_bp)
    register_error_handlers(app)
    return app
