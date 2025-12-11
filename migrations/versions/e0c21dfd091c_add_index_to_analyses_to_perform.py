"""add_index_to_analyses_to_perform

Revision ID: e0c21dfd091c
Revises: c2540af885c6
Create Date: 2025-12-03 05:57:07.957347

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0c21dfd091c'
down_revision = 'c2540af885c6'
branch_labels = None
depends_on = None


def upgrade():
    """Sample.analyses_to_perform баганад index нэмэх (query performance сайжруулах)"""
    op.create_index('ix_sample_analyses_to_perform', 'sample', ['analyses_to_perform'])


def downgrade():
    """Index устгах"""
    op.drop_index('ix_sample_analyses_to_perform', table_name='sample')
