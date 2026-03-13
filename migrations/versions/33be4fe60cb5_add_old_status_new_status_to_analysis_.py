"""add old_status new_status to analysis_result_log

Revision ID: 33be4fe60cb5
Revises: f72fa7d1888d
Create Date: 2026-03-12 13:42:02.594432

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '33be4fe60cb5'
down_revision = 'f72fa7d1888d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('analysis_result_log', schema=None) as batch_op:
        batch_op.add_column(sa.Column('old_status', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('new_status', sa.String(length=50), nullable=True))


def downgrade():
    with op.batch_alter_table('analysis_result_log', schema=None) as batch_op:
        batch_op.drop_column('new_status')
        batch_op.drop_column('old_status')
