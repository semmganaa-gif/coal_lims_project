"""add audit trail ip_address source_endpoint old_new_value columns

Revision ID: f72fa7d1888d
Revises: 288c26079520
Create Date: 2026-03-12 13:09:59.424104

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f72fa7d1888d'
down_revision = '288c26079520'
branch_labels = None
depends_on = None


def upgrade():
    # AnalysisResultLog: IP address, source endpoint, previous value
    with op.batch_alter_table('analysis_result_log', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ip_address', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('source_endpoint', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('previous_value', sa.Float(), nullable=True))

    # AuditLog: before/after values
    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.add_column(sa.Column('old_value', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('new_value', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.drop_column('new_value')
        batch_op.drop_column('old_value')

    with op.batch_alter_table('analysis_result_log', schema=None) as batch_op:
        batch_op.drop_column('previous_value')
        batch_op.drop_column('source_endpoint')
        batch_op.drop_column('ip_address')
