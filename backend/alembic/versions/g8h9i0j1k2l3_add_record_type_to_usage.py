"""Add record_type to usage_records for distinguishing adjustments.

Revision ID: g8h9i0j1k2l3
Revises: f7g8h9i0j1k2
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa


revision = "g8h9i0j1k2l3"
down_revision = "f7g8h9i0j1k2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usage_records",
        sa.Column(
            "record_type",
            sa.String(20),
            nullable=False,
            server_default="usage",
        ),
    )
    op.add_column(
        "usage_records",
        sa.Column("note", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("usage_records", "note")
    op.drop_column("usage_records", "record_type")
