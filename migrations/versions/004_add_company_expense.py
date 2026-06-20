"""Add company expense table."""

from alembic import op
import sqlalchemy as sa


revision = "004_add_company_expense"
down_revision = "003_add_user_driver_commission_ratio"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "company_expense",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("company_expense")
