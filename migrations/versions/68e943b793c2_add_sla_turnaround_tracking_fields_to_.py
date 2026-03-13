"""add SLA turnaround tracking fields to Sample

Revision ID: 68e943b793c2
Revises: fe06d9cc1e7b
Create Date: 2026-03-12 11:00:24.382214

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '68e943b793c2'
down_revision = 'fe06d9cc1e7b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('sample', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sla_hours', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('due_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('priority', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('completed_at', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_sample_due_date'), ['due_date'], unique=False)


def downgrade():
    with op.batch_alter_table('sample', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_sample_due_date'))
        batch_op.drop_column('completed_at')
        batch_op.drop_column('priority')
        batch_op.drop_column('due_date')
        batch_op.drop_column('sla_hours')
