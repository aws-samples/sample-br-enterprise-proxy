"""Add monthly quota, daily limit, reset policy, and quota start to api_tokens.

Revision ID: f7g8h9i0j1k2
Revises: e6f7g8h9i0j1
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa


revision = "f7g8h9i0j1k2"
down_revision = "e6f7g8h9i0j1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "api_tokens",
        sa.Column("monthly_quota_usd", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "api_tokens",
        sa.Column("monthly_reset_policy", sa.String(20), nullable=True),
    )
    op.add_column(
        "api_tokens",
        sa.Column("monthly_quota_start", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("api_tokens", "monthly_quota_start")
    op.drop_column("api_tokens", "monthly_reset_policy")
    op.drop_column("api_tokens", "monthly_quota_usd")
