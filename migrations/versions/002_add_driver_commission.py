"""Add driver commission fields."""

from alembic import op
import sqlalchemy as sa


revision = "002_add_driver_commission"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("setting", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "driver_commission_ratio",
                sa.Float(),
                nullable=True,
                server_default="0.75"
            )
        )

    with op.batch_alter_table("order", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "driver_commission",
                sa.Float(),
                nullable=True,
                server_default="0"
            )
        )

    op.execute(
        """
        UPDATE "order"
        SET driver_commission = ROUND(commission * 0.75, 2)
        WHERE driver_commission IS NULL OR driver_commission = 0
        """
    )

    op.execute(
        """
        UPDATE setting
        SET driver_commission_ratio = 0.75
        WHERE driver_commission_ratio IS NULL
        """
    )


def downgrade():
    with op.batch_alter_table("order", schema=None) as batch_op:
        batch_op.drop_column("driver_commission")

    with op.batch_alter_table("setting", schema=None) as batch_op:
        batch_op.drop_column("driver_commission_ratio")
