"""Add shop delivery discount ratio."""

from alembic import op
import sqlalchemy as sa


revision = "006_add_shop_discount_ratio"
down_revision = "005_add_operator_permissions"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("shop", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "discount_ratio",
                sa.Float(),
                nullable=True,
            )
        )

    op.execute(
        """
        UPDATE shop
        SET discount_ratio = 0
        WHERE discount_ratio IS NULL
        """
    )


def downgrade():
    with op.batch_alter_table("shop", schema=None) as batch_op:
        batch_op.drop_column(
            "discount_ratio"
        )
