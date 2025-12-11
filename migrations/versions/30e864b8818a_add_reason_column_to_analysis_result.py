"""add_reason_column_to_analysis_result

Revision ID: 30e864b8818a
Revises: 332291bdbdc1
Create Date: 2025-12-11 13:55:17.980051

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30e864b8818a'
down_revision = '332291bdbdc1'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import text
    conn = op.get_bind()

    # analysis_result хүснэгтэд дутуу баганууд нэмэх (IF NOT EXISTS)
    conn.execute(text("""
        DO $$ BEGIN
            ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS reason TEXT;
            ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS error_reason VARCHAR(50);
        END $$;
    """))

    # analysis_result_log хүснэгтэд мөн
    conn.execute(text("""
        DO $$ BEGIN
            ALTER TABLE analysis_result_log ADD COLUMN IF NOT EXISTS reason VARCHAR(255);
            ALTER TABLE analysis_result_log ADD COLUMN IF NOT EXISTS error_reason VARCHAR(50);
        END $$;
    """))


def downgrade():
    op.drop_column('analysis_result', 'error_reason')
    op.drop_column('analysis_result', 'reason')
    op.drop_column('analysis_result_log', 'error_reason')
    op.drop_column('analysis_result_log', 'reason')
