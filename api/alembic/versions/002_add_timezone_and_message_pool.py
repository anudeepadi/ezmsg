"""Add timezone to participants and message_pool to sms_keywords.

Revision ID: 002
Revises: 001
Create Date: 2026-02-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add timezone column to participants (default America/Chicago)
    op.add_column(
        "participants",
        sa.Column("timezone", sa.String(50), nullable=False, server_default="America/Chicago"),
    )

    # Add message_pool JSON column to sms_keywords (for HELPNOW rotating pools)
    op.add_column(
        "sms_keywords",
        sa.Column("message_pool", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sms_keywords", "message_pool")
    op.drop_column("participants", "timezone")
