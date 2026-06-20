"""
Database management CLI.

Edit schema in app/models.py, then run:

    python manage.py db migrate -m "describe your change"
    python manage.py db upgrade

Never edit delivery.db manually.
"""

import click
from flask.cli import FlaskGroup

from app import create_app, db
from app.models import (
    ActivityLog,
    DriverLedger,
    Order,
    Place,
    RouteCommission,
    Setting,
    Shop,
    User,
)


def create_app_for_cli():
    return create_app()


@click.group(cls=FlaskGroup, create_app=create_app_for_cli)
def cli():
    """Manage the delivery application and database."""


@cli.command("seed")
def seed_defaults():
    """Insert default settings and demo users if they are missing."""

    from werkzeug.security import generate_password_hash

    if not Setting.query.first():
        db.session.add(Setting(default_commission=3, driver_commission_ratio=0.75))
        db.session.commit()
        click.echo("Created default settings.")

    if not User.query.filter_by(username="admin").first():
        db.session.add_all([
            User(
                username="admin",
                full_name="Administrator",
                role="admin",
                password_hash=generate_password_hash("admin123"),
            ),
            User(
                username="operator",
                full_name="Operator",
                role="operator",
                password_hash=generate_password_hash("op123"),
            ),
            User(
                username="driver1",
                full_name="Driver One",
                role="driver",
                password_hash=generate_password_hash("d123"),
            ),
        ])
        db.session.commit()
        click.echo("Created default users.")


if __name__ == "__main__":
    cli()
