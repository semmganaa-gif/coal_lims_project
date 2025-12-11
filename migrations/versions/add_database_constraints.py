"""Add database constraints

Revision ID: add_constraints_001
Revises: 96e8bcf13076
Create Date: 2025-01-15 10:00:00.000000

Энэ migration нь зөвхөн байгаа баганууд дээр constraint нэмнэ.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_constraints_001'
down_revision = '96e8bcf13076'
branch_labels = None
depends_on = None


def upgrade():
    """
    Database constraints нэмэх - зөвхөн байгаа баганууд дээр
    """
    from sqlalchemy import text
    conn = op.get_bind()

    # Sample indexes
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sample_received_date ON sample (received_date)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sample_status ON sample (status)"))

    # AnalysisResult indexes
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analysis_result_sample_id ON analysis_result (sample_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analysis_result_status ON analysis_result (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analysis_result_created_at ON analysis_result (created_at)"))

    # AuditLog indexes (if table exists)
    conn.execute(text("""
        DO $$ BEGIN
            CREATE INDEX IF NOT EXISTS ix_audit_log_timestamp ON audit_log (timestamp);
        EXCEPTION WHEN undefined_table THEN NULL;
        END $$;
    """))
    conn.execute(text("""
        DO $$ BEGIN
            CREATE INDEX IF NOT EXISTS ix_audit_log_action ON audit_log (action);
        EXCEPTION WHEN undefined_table THEN NULL;
        END $$;
    """))
    conn.execute(text("""
        DO $$ BEGIN
            CREATE INDEX IF NOT EXISTS ix_audit_log_user_id ON audit_log (user_id);
        EXCEPTION WHEN undefined_table THEN NULL;
        END $$;
    """))


def downgrade():
    """
    Constraints устгах (rollback)
    """
    from sqlalchemy import text
    conn = op.get_bind()

    conn.execute(text("DROP INDEX IF EXISTS ix_audit_log_user_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_audit_log_action"))
    conn.execute(text("DROP INDEX IF EXISTS ix_audit_log_timestamp"))
    conn.execute(text("DROP INDEX IF EXISTS ix_analysis_result_created_at"))
    conn.execute(text("DROP INDEX IF EXISTS ix_analysis_result_status"))
    conn.execute(text("DROP INDEX IF EXISTS ix_analysis_result_sample_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_sample_status"))
    conn.execute(text("DROP INDEX IF EXISTS ix_sample_received_date"))
