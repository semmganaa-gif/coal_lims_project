"""add instrument_reading table

Revision ID: 288c26079520
Revises: 68e943b793c2
Create Date: 2026-03-12 11:26:12.702659

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '288c26079520'
down_revision = '68e943b793c2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('instrument_reading',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('equipment_id', sa.Integer(), nullable=True),
    sa.Column('instrument_name', sa.String(length=100), nullable=False),
    sa.Column('instrument_type', sa.String(length=50), nullable=False),
    sa.Column('source_file', sa.String(length=500), nullable=False),
    sa.Column('file_hash', sa.String(length=64), nullable=True),
    sa.Column('sample_id', sa.Integer(), nullable=True),
    sa.Column('sample_code', sa.String(length=100), nullable=True),
    sa.Column('analysis_code', sa.String(length=20), nullable=True),
    sa.Column('raw_data', sa.JSON(), nullable=True),
    sa.Column('parsed_value', sa.Float(), nullable=True),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('reviewed_by_id', sa.Integer(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('reject_reason', sa.String(length=200), nullable=True),
    sa.Column('analysis_result_id', sa.Integer(), nullable=True),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['analysis_result_id'], ['analysis_result.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
    sa.ForeignKeyConstraint(['reviewed_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['sample_id'], ['sample.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('instrument_reading', schema=None) as batch_op:
        batch_op.create_index('ix_instr_reading_status_read_at', ['status', 'read_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_instrument_reading_analysis_code'), ['analysis_code'], unique=False)
        batch_op.create_index(batch_op.f('ix_instrument_reading_equipment_id'), ['equipment_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_instrument_reading_read_at'), ['read_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_instrument_reading_sample_code'), ['sample_code'], unique=False)
        batch_op.create_index(batch_op.f('ix_instrument_reading_sample_id'), ['sample_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_instrument_reading_status'), ['status'], unique=False)


def downgrade():
    with op.batch_alter_table('instrument_reading', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_instrument_reading_status'))
        batch_op.drop_index(batch_op.f('ix_instrument_reading_sample_id'))
        batch_op.drop_index(batch_op.f('ix_instrument_reading_sample_code'))
        batch_op.drop_index(batch_op.f('ix_instrument_reading_read_at'))
        batch_op.drop_index(batch_op.f('ix_instrument_reading_equipment_id'))
        batch_op.drop_index(batch_op.f('ix_instrument_reading_analysis_code'))
        batch_op.drop_index('ix_instr_reading_status_read_at')

    op.drop_table('instrument_reading')
