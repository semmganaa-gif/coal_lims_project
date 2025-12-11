"""rename_roles_himich_beltgegch_add_manager

Revision ID: c3bc04cf9877
Revises: b3ed3b177364
Create Date: 2025-12-04 02:38:37.453185

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3bc04cf9877'
down_revision = 'b3ed3b177364'
branch_labels = None
depends_on = None


def upgrade():
    """
    Rename roles:
    - himich -> chemist
    - beltgegch -> prep
    Also update AnalysisType.required_role
    """
    # Update user roles
    op.execute("UPDATE user SET role = 'chemist' WHERE role = 'himich'")
    op.execute("UPDATE user SET role = 'prep' WHERE role = 'beltgegch'")

    # Update analysis_type required_role
    op.execute("UPDATE analysis_type SET required_role = 'chemist' WHERE required_role = 'himich'")
    op.execute("UPDATE analysis_type SET required_role = 'prep' WHERE required_role = 'beltgegch'")


def downgrade():
    """Revert role renames."""
    # Revert user roles
    op.execute("UPDATE user SET role = 'himich' WHERE role = 'chemist'")
    op.execute("UPDATE user SET role = 'beltgegch' WHERE role = 'prep'")

    # Revert analysis_type required_role
    op.execute("UPDATE analysis_type SET required_role = 'himich' WHERE required_role = 'chemist'")
    op.execute("UPDATE analysis_type SET required_role = 'beltgegch' WHERE required_role = 'prep'")
