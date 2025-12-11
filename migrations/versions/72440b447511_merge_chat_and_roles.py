"""merge_chat_and_roles

Revision ID: 72440b447511
Revises: add_chat_tables, c3bc04cf9877
Create Date: 2025-12-11 13:51:32.433017

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72440b447511'
down_revision = ('add_chat_tables', 'c3bc04cf9877')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
