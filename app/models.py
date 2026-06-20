from datetime import datetime

from . import db

"""
Edit models here, then run:

    python manage.py db migrate -m "describe change"
    python manage.py db upgrade

Do not edit delivery.db manually.
"""


class Setting(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    default_commission = db.Column(
        db.Float,
        default=3
    )

    driver_commission_ratio = db.Column(
        db.Float,
        default=0.75
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    full_name = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Available"
    )

    balance = db.Column(
        db.Float,
        default=0
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    driver_commission_ratio = db.Column(
        db.Float,
        default=0.75
    )

    operator_permissions = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class Place(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

class Shop(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(255),
        unique=True
    )

    phone = db.Column(
        db.String(100)
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    place_id = db.Column(
        db.Integer,
        db.ForeignKey("place.id")
    )

    place = db.relationship(
        "Place"
    )

    location_details = db.Column(
        db.Text
    )


class Order(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    shop_id = db.Column(
        db.Integer,
        db.ForeignKey("shop.id")
    )

    driver_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    shop = db.relationship(
        "Shop"
    )

    driver = db.relationship(
        "User"
    )

    customer_name = db.Column(
        db.String(255)
    )

    customer_phone = db.Column(
        db.String(100)
    )

    shop_location = db.Column(
        db.Text
    )

    delivery_location = db.Column(
        db.Text
    )

    amount_paid_to_shop = db.Column(
        db.Float,
        default=0
    )

    amount_received_from_customer = db.Column(
        db.Float,
        default=0
    )

    destination = db.Column(
        db.Text
    )

    notes = db.Column(
        db.Text
    )

    order_total = db.Column(
        db.Float,
        default=0
    )

    commission = db.Column(
        db.Float,
        default=3
    )

    driver_commission = db.Column(
        db.Float,
        default=0
    )

    payment_type = db.Column(
        db.String(20)
    )

    status = db.Column(
        db.String(50),
        default="Pending"
    )

    decline_reason = db.Column(
        db.Text
    )

    created_by = db.Column(
        db.String(100)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    destination_place_id = db.Column(
        db.Integer,
        db.ForeignKey("place.id")
    )

    destination_place = db.relationship(
        "Place"
    )



class DriverLedger(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    driver_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("order.id")
    )

    driver = db.relationship(
        "User"
    )

    order = db.relationship(
        "Order"
    )

    transaction_type = db.Column(
        db.String(50)
    )

    amount = db.Column(
        db.Float
    )

    balance_after = db.Column(
        db.Float
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class CompanyExpense(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    description = db.Column(
        db.String(255),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    category = db.Column(
        db.String(50),
        default="أخرى"
    )

    expense_date = db.Column(
        db.Date,
        nullable=False
    )

    notes = db.Column(
        db.Text
    )

    created_by = db.Column(
        db.String(100)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class ActivityLog(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100)
    )

    action = db.Column(
        db.String(255)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class RouteCommission(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    from_place_id = db.Column(
        db.Integer,
        db.ForeignKey("place.id")
    )

    to_place_id = db.Column(
        db.Integer,
        db.ForeignKey("place.id")
    )

    commission = db.Column(
        db.Float,
        default=0
    )

    from_place = db.relationship(
        "Place",
        foreign_keys=[from_place_id]
    )

    to_place = db.relationship(
        "Place",
        foreign_keys=[to_place_id]
    )