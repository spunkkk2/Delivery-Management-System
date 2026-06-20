"""Initial database schema."""

from alembic import op
import sqlalchemy as sa


revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "setting",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("default_commission", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=True),
        sa.Column("balance", sa.Float(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "place",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "activity_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "shop",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("place_id", sa.Integer(), nullable=True),
        sa.Column("location_details", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["place_id"], ["place.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "route_commission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("from_place_id", sa.Integer(), nullable=True),
        sa.Column("to_place_id", sa.Integer(), nullable=True),
        sa.Column("commission", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["from_place_id"], ["place.id"]),
        sa.ForeignKeyConstraint(["to_place_id"], ["place.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "order",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shop_id", sa.Integer(), nullable=True),
        sa.Column("driver_id", sa.Integer(), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("customer_phone", sa.String(length=100), nullable=True),
        sa.Column("shop_location", sa.Text(), nullable=True),
        sa.Column("delivery_location", sa.Text(), nullable=True),
        sa.Column("amount_paid_to_shop", sa.Float(), nullable=True),
        sa.Column("amount_received_from_customer", sa.Float(), nullable=True),
        sa.Column("destination", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("order_total", sa.Float(), nullable=True),
        sa.Column("commission", sa.Float(), nullable=True),
        sa.Column("payment_type", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("decline_reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("destination_place_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["destination_place_id"], ["place.id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["shop_id"], ["shop.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "driver_ledger",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("transaction_type", sa.String(length=50), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("balance_after", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["driver_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["order.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("driver_ledger")
    op.drop_table("order")
    op.drop_table("route_commission")
    op.drop_table("shop")
    op.drop_table("activity_log")
    op.drop_table("place")
    op.drop_table("user")
    op.drop_table("setting")
