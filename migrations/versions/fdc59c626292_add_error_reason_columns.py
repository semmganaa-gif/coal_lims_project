"""add_error_reason_columns

Revision ID: fdc59c626292
Revises: 30e864b8818a
Create Date: 2025-12-11 13:56:38.192546

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fdc59c626292'
down_revision = '30e864b8818a'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import text
    conn = op.get_bind()

    # error_reason баганууд нэмэх (IF NOT EXISTS)
    conn.execute(text("""
        ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS error_reason VARCHAR(50);
    """))
    conn.execute(text("""
        ALTER TABLE analysis_result_log ADD COLUMN IF NOT EXISTS reason VARCHAR(255);
    """))
    conn.execute(text("""
        ALTER TABLE analysis_result_log ADD COLUMN IF NOT EXISTS error_reason VARCHAR(50);
    """))


def downgrade():
    op.drop_column('analysis_result', 'error_reason')
    op.drop_column('analysis_result_log', 'error_reason')
    op.drop_column('analysis_result_log', 'reason')
