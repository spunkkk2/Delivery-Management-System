"""
Database models — edit this file to change the schema safely.

Workflow (never edit delivery.db manually):

1. Add or change columns/tables in app/models.py
2. Create a migration:
       python manage.py db migrate -m "add phone to shop"
3. Apply it:
       python manage.py db upgrade

Other useful commands:

    python manage.py db current     # show current migration
    python manage.py db history     # list all migrations
    python manage.py seed           # insert default users/settings
    python manage.py db downgrade   # undo last migration

Fresh install on a new machine:

    pip install -r requirements.txt
    python manage.py db upgrade
    python manage.py seed
    python run.py
"""

from app.models import (  # noqa: F401
    ActivityLog,
    DriverLedger,
    Order,
    Place,
    RouteCommission,
    Setting,
    Shop,
    User,
)

__all__ = [
    "ActivityLog",
    "DriverLedger",
    "Order",
    "Place",
    "RouteCommission",
    "Setting",
    "Shop",
    "User",
]
