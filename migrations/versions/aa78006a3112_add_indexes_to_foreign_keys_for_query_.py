"""Add indexes to foreign keys for query performance

Revision ID: aa78006a3112
Revises: 96e8bcf13076
Create Date: 2025-11-30 05:32:44.636561

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa78006a3112'
down_revision = '96e8bcf13076'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import text
    conn = op.get_bind()

    # PostgreSQL-д IF NOT EXISTS ашиглана
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analysis_result_sample_id ON analysis_result (sample_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analysis_result_user_id ON analysis_result (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analysis_result_log_user_id ON analysis_result_log (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bottle_created_by_id ON bottle (created_by_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bottle_constant_approved_by_id ON bottle_constant (approved_by_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bottle_constant_created_by_id ON bottle_constant (created_by_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sample_user_id ON sample (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_system_setting_updated_by_id ON system_setting (updated_by_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_usage_logs_sample_id ON usage_logs (sample_id)"))


def downgrade():
    from sqlalchemy import text
    conn = op.get_bind()

    conn.execute(text("DROP INDEX IF EXISTS ix_usage_logs_sample_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_system_setting_updated_by_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_sample_user_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_bottle_constant_created_by_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_bottle_constant_approved_by_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_bottle_created_by_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_analysis_result_log_user_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_analysis_result_user_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_analysis_result_sample_id"))
