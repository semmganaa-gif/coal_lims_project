"""Add lab_type columns for multi-lab support

Revision ID: 202601300001
Revises: 202601110131
Create Date: 2026-01-30
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '202601300001'
down_revision = '202601110131'
branch_labels = None
depends_on = None


def upgrade():
    # Sample моделд lab_type нэмэх
    with op.batch_alter_table('sample', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lab_type', sa.String(20), server_default='coal', nullable=True))
        batch_op.create_index('ix_sample_lab_type', ['lab_type'])

    # AnalysisType моделд lab_type нэмэх
    with op.batch_alter_table('analysis_type', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lab_type', sa.String(20), server_default='coal', nullable=True))
        batch_op.create_index('ix_analysis_type_lab_type', ['lab_type'])

    # User моделд allowed_labs нэмэх
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('allowed_labs', sa.JSON(), nullable=True))

    # Одоо байгаа бүх бичлэгүүдийг 'coal' болгох
    op.execute("UPDATE sample SET lab_type = 'coal' WHERE lab_type IS NULL")
    op.execute("UPDATE analysis_type SET lab_type = 'coal' WHERE lab_type IS NULL")


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('allowed_labs')

    with op.batch_alter_table('analysis_type', schema=None) as batch_op:
        batch_op.drop_index('ix_analysis_type_lab_type')
        batch_op.drop_column('lab_type')

    with op.batch_alter_table('sample', schema=None) as batch_op:
        batch_op.drop_index('ix_sample_lab_type')
        batch_op.drop_column('lab_type')
