"""rename_role_ahlah_to_senior

Revision ID: b3ed3b177364
Revises: e0c21dfd091c
Create Date: 2025-12-04 02:29:49.334169

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3ed3b177364'
down_revision = 'e0c21dfd091c'
branch_labels = None
depends_on = None


def upgrade():
    """Rename 'ahlah' role to 'senior' for all users."""
    # Update user roles from 'ahlah' to 'senior'
    op.execute("UPDATE user SET role = 'senior' WHERE role = 'ahlah'")


def downgrade():
    """Revert 'senior' role back to 'ahlah'."""
    op.execute("UPDATE user SET role = 'ahlah' WHERE role = 'senior'")
