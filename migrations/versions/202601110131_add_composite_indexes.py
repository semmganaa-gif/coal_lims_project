"""Add composite indexes for query performance

Revision ID: 202601110131
Revises: 0128b9f78ffc
Create Date: 2026-01-11

Composite indexes нэмж query хурдыг сайжруулна:
- analysis_result: sample_id+analysis_code, sample_id+status, etc.
- analysis_result_log: analysis_code+timestamp, sample_id+timestamp, etc.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '202601110131'
down_revision = '0128b9f78ffc'
branch_labels = None
depends_on = None


def upgrade():
    # AnalysisResult composite indexes
    op.create_index(
        'ix_analysis_result_sample_code',
        'analysis_result',
        ['sample_id', 'analysis_code'],
        unique=False
    )
    op.create_index(
        'ix_analysis_result_sample_status',
        'analysis_result',
        ['sample_id', 'status'],
        unique=False
    )
    op.create_index(
        'ix_analysis_result_code_status',
        'analysis_result',
        ['analysis_code', 'status'],
        unique=False
    )
    op.create_index(
        'ix_analysis_result_user_code',
        'analysis_result',
        ['user_id', 'analysis_code'],
        unique=False
    )

    # AnalysisResultLog composite indexes
    op.create_index(
        'ix_result_log_code_timestamp',
        'analysis_result_log',
        ['analysis_code', 'timestamp'],
        unique=False
    )
    op.create_index(
        'ix_result_log_sample_timestamp',
        'analysis_result_log',
        ['sample_id', 'timestamp'],
        unique=False
    )
    op.create_index(
        'ix_result_log_user_timestamp',
        'analysis_result_log',
        ['user_id', 'timestamp'],
        unique=False
    )


def downgrade():
    # AnalysisResultLog indexes
    op.drop_index('ix_result_log_user_timestamp', table_name='analysis_result_log')
    op.drop_index('ix_result_log_sample_timestamp', table_name='analysis_result_log')
    op.drop_index('ix_result_log_code_timestamp', table_name='analysis_result_log')

    # AnalysisResult indexes
    op.drop_index('ix_analysis_result_user_code', table_name='analysis_result')
    op.drop_index('ix_analysis_result_code_status', table_name='analysis_result')
    op.drop_index('ix_analysis_result_sample_status', table_name='analysis_result')
    op.drop_index('ix_analysis_result_sample_code', table_name='analysis_result')
