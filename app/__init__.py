from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app():

    app = Flask(__name__)

    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)

    from . import models  # noqa: F401 — register models for migrations

    from .auth import auth_bp
    from .admin import admin_bp
    from .operator import operator_bp
    from .driver import driver_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(operator_bp)
    app.register_blueprint(driver_bp)

    @app.context_processor
    def inject_layout_context():

        from flask import request
        from .decorators import current_user

        from .permissions import (
            parse_operator_permissions,
            OPERATOR_PAGES,
            ALL_OPERATOR_PERMISSIONS,
        )

        user = current_user()

        is_operator_section = (
            request.blueprint == "operator"
        )

        is_admin_section = (
            request.blueprint == "admin"
        )

        is_arabic_rtl = (
            is_operator_section
            or is_admin_section
            or (
                user is not None
                and user.role == "admin"
                and request.blueprint != "driver"
            )
        )

        is_login_page = (
            request.endpoint == "auth.login"
        )

        operator_permissions = []

        if user and user.role in (
            "operator",
            "admin",
        ):
            operator_permissions = (
                parse_operator_permissions(
                    user
                )
                if user.role == "operator"
                else ALL_OPERATOR_PERMISSIONS
            )

        return {
            "user": user,
            "is_operator_section": is_operator_section,
            "is_admin_section": is_admin_section,
            "is_arabic_rtl": is_arabic_rtl,
            "is_login_page": is_login_page,
            "operator_permissions": (
                operator_permissions
            ),
            "operator_pages": OPERATOR_PAGES,
        }

    return app


def seed_defaults():

    from werkzeug.security import generate_password_hash
    from .models import Setting, User

    if not Setting.query.first():
        db.session.add(
            Setting(
                default_commission=3,
                driver_commission_ratio=0.75
            )
        )
        db.session.commit()

    if not User.query.filter_by(
        username="admin"
    ).first():

        admin = User(
            username="admin",
            full_name="Administrator",
            role="admin",
            password_hash=generate_password_hash(
                "admin123"
            )
        )

        operator = User(
            username="operator",
            full_name="Operator",
            role="operator",
            password_hash=generate_password_hash(
                "op123"
            )
        )

        driver = User(
            username="driver1",
            full_name="Driver One",
            role="driver",
            password_hash=generate_password_hash(
                "d123"
            )
        )

        db.session.add(admin)
        db.session.add(operator)
        db.session.add(driver)
        db.session.commit()