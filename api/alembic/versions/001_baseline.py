"""Baseline migration — captures existing schema.

This is a retroactive migration that establishes Alembic tracking on the
existing database. It does NOT create tables (they already exist via
init_db.py). When running on a fresh database, use init_db.py first, then
stamp this revision with: alembic stamp 001

Revision ID: 001
Revises: None
Create Date: 2026-02-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is a baseline migration. The schema already exists.
    # On a fresh database, init_db.py creates the tables, and then
    # you run `alembic stamp 001` to mark this revision as applied.
    #
    # Tables captured at this baseline:
    #   users, refresh_tokens, projects, project_users,
    #   participants, participant_variable_values,
    #   variables, message_templates, message_template_texts,
    #   message_template_variables, messaging_nodes, messaging_node_edges,
    #   timing_elements, conditional_expressions,
    #   conditional_expression_variables, scheduled_messages,
    #   incoming_messages, sms_keywords, available_languages
    #
    # Enum types: user_role, project_status
    pass


def downgrade() -> None:
    # Cannot downgrade from baseline
    raise RuntimeError("Cannot downgrade past the baseline migration.")
