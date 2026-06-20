"""Add operator permissions column."""

from alembic import op
import sqlalchemy as sa


revision = "005_add_operator_permissions"
down_revision = "004_add_company_expense"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "operator_permissions",
                sa.Text(),
                nullable=True,
            )
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column(
            "operator_permissions"
        )
