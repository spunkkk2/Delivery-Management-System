"""Add per-driver commission ratio."""

from alembic import op
import sqlalchemy as sa


revision = "003_add_user_driver_commission_ratio"
down_revision = "002_add_driver_commission"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "driver_commission_ratio",
                sa.Float(),
                nullable=True,
                server_default="0.75",
            )
        )

    op.execute(
        """
        UPDATE user
        SET driver_commission_ratio = 0.75
        WHERE role = 'driver'
          AND driver_commission_ratio IS NULL
        """
    )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("driver_commission_ratio")
