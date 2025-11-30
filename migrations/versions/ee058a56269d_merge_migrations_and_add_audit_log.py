"""merge_migrations_and_add_audit_log

Revision ID: ee058a56269d
Revises: aa78006a3112, add_constraints_001
Create Date: 2025-11-30 10:40:01.143737

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee058a56269d'
down_revision = ('aa78006a3112', 'add_constraints_001')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
