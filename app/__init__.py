import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from sqlalchemy.exc import OperationalError

from .extensions import db, migrate
from .routes import main_bp
from .services.data_seed import seed_data


def configure_logging(app):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    app.logger.setLevel(logging.INFO)


def reset_sqlite_demo_database(app):
    if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
        return
    if os.getenv("DEMO_RESET_DB", "false").lower() != "true":
        return

    db_name = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "", 1)
    db_path = Path(app.instance_path) / db_name
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        if request.is_json:
            return jsonify({"ok": False, "message": "Resource not found."}), 404
        return render_template(
            "error.html",
            title="Page not found",
            message="The page you requested could not be found.",
        ), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception("Unhandled application error: %s", error)
        if request.is_json:
            return jsonify({"ok": False, "message": "Something went wrong on our side."}), 500
        return render_template(
            "error.html",
            title="Server error",
            message="Something went wrong. Please try again.",
        ), 500


def create_app():
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    database_url = os.getenv("DATABASE_URL", "sqlite:///food_ordering.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["ADMIN_EMAIL"] = os.getenv("ADMIN_EMAIL", "admin@foodsprint.local")
    app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "admin123")
    app.config["FOODSPRINT_UPI_ID"] = os.getenv("FOODSPRINT_UPI_ID", "foodsprint@upi")
    app.config["STAFF_LIMIT"] = int(os.getenv("STAFF_LIMIT", "3"))
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"

    configure_logging(app)
    reset_sqlite_demo_database(app)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from . import models  # noqa: F401

        try:
            db.create_all()
            seed_data()
        except OperationalError:
            if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
                db_name = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "", 1)
                db_path = Path(app.instance_path) / db_name
                if db_path.exists():
                    db_path.unlink()
                db.drop_all()
                db.create_all()
                seed_data()
            else:
                raise

    app.register_blueprint(main_bp)
    register_error_handlers(app)
    return app
