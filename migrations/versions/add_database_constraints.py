"""Add database constraints

Revision ID: add_constraints_001
Revises:
Create Date: 2025-01-15 10:00:00.000000

Үүнд:
- Unique constraints
- Foreign key constraints
- Check constraints
- Index-үүд

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_constraints_001'
down_revision = None  # Өмнөх migration-ий ID-г оруулах
branch_labels = None
depends_on = None


def upgrade():
    """
    Database constraints нэмэх

    АНХААРУУЛГА:
    - Энэ migration ажиллуулахаас өмнө өгөгдөл шалгах хэрэгтэй
    - Давхцсан өгөгдөл байвал constraint үүсэхгүй
    """

    # ========================================================
    # 1. UNIQUE CONSTRAINTS
    # ========================================================

    # Sample - sample_code unique
    try:
        op.create_unique_constraint(
            'uq_sample_code',
            'sample',
            ['sample_code']
        )
    except Exception:
        # Constraint аль хэдийн байвал алдаа өгөхгүй
        pass

    # AnalysisResult - (sample_id, analysis_code) unique
    try:
        op.create_unique_constraint(
            'uq_sample_analysis',
            'analysis_result',
            ['sample_id', 'analysis_code']
        )
    except Exception:
        pass

    # User - username unique
    try:
        op.create_unique_constraint(
            'uq_user_username',
            'user',
            ['username']
        )
    except Exception:
        pass

    # Equipment - equipment_code unique
    try:
        op.create_unique_constraint(
            'uq_equipment_code',
            'equipment',
            ['equipment_code']
        )
    except Exception:
        pass

    # ========================================================
    # 2. FOREIGN KEY CONSTRAINTS
    # ========================================================

    # AnalysisResult -> Sample
    try:
        op.create_foreign_key(
            'fk_analysis_result_sample',
            'analysis_result',
            'sample',
            ['sample_id'],
            ['id'],
            ondelete='CASCADE'  # Sample устгахад analysis result-ууд ч устана
        )
    except Exception:
        pass

    # AnalysisResult -> User (created_by)
    try:
        op.create_foreign_key(
            'fk_analysis_result_created_by',
            'analysis_result',
            'user',
            ['created_by_id'],
            ['id'],
            ondelete='SET NULL'  # User устгахад created_by_id NULL болно
        )
    except Exception:
        pass

    # AnalysisResult -> User (reviewed_by)
    try:
        op.create_foreign_key(
            'fk_analysis_result_reviewed_by',
            'analysis_result',
            'user',
            ['reviewed_by_id'],
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        pass

    # AnalysisResult -> Equipment
    try:
        op.create_foreign_key(
            'fk_analysis_result_equipment',
            'analysis_result',
            'equipment',
            ['equipment_id'],
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        pass

    # ========================================================
    # 3. CHECK CONSTRAINTS
    # ========================================================

    # Sample - weight > 0
    try:
        op.create_check_constraint(
            'ck_sample_weight_positive',
            'sample',
            'weight IS NULL OR weight > 0'
        )
    except Exception:
        pass

    # Sample - mass > 0
    try:
        op.create_check_constraint(
            'ck_sample_mass_positive',
            'sample',
            'mass IS NULL OR mass > 0'
        )
    except Exception:
        pass

    # AnalysisResult - status valid
    try:
        op.create_check_constraint(
            'ck_analysis_result_status',
            'analysis_result',
            "status IN ('pending_review', 'approved', 'rejected', 'draft')"
        )
    except Exception:
        pass

    # User - role valid
    try:
        op.create_check_constraint(
            'ck_user_role',
            'user',
            "role IN ('beltgegch', 'himich', 'ahlah', 'senior', 'admin')"
        )
    except Exception:
        pass

    # ========================================================
    # 4. INDEXES (Performance optimization)
    # ========================================================

    # Sample indexes
    try:
        op.create_index('ix_sample_received_date', 'sample', ['received_date'])
    except Exception:
        pass

    try:
        op.create_index('ix_sample_status', 'sample', ['status'])
    except Exception:
        pass

    # AnalysisResult indexes
    try:
        op.create_index('ix_analysis_result_sample_id', 'analysis_result', ['sample_id'])
    except Exception:
        pass

    try:
        op.create_index('ix_analysis_result_status', 'analysis_result', ['status'])
    except Exception:
        pass

    try:
        op.create_index('ix_analysis_result_created_at', 'analysis_result', ['created_at'])
    except Exception:
        pass

    # AuditLog indexes
    try:
        op.create_index('ix_audit_log_timestamp', 'audit_log', ['timestamp'])
    except Exception:
        pass

    try:
        op.create_index('ix_audit_log_action', 'audit_log', ['action'])
    except Exception:
        pass

    try:
        op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])
    except Exception:
        pass


def downgrade():
    """
    Constraints устгах (rollback)
    """

    # Drop indexes
    try:
        op.drop_index('ix_audit_log_user_id', 'audit_log')
        op.drop_index('ix_audit_log_action', 'audit_log')
        op.drop_index('ix_audit_log_timestamp', 'audit_log')
        op.drop_index('ix_analysis_result_created_at', 'analysis_result')
        op.drop_index('ix_analysis_result_status', 'analysis_result')
        op.drop_index('ix_analysis_result_sample_id', 'analysis_result')
        op.drop_index('ix_sample_status', 'sample')
        op.drop_index('ix_sample_received_date', 'sample')
    except Exception:
        pass

    # Drop check constraints
    try:
        op.drop_constraint('ck_user_role', 'user', type_='check')
        op.drop_constraint('ck_analysis_result_status', 'analysis_result', type_='check')
        op.drop_constraint('ck_sample_mass_positive', 'sample', type_='check')
        op.drop_constraint('ck_sample_weight_positive', 'sample', type_='check')
    except Exception:
        pass

    # Drop foreign keys
    try:
        op.drop_constraint('fk_analysis_result_equipment', 'analysis_result', type_='foreignkey')
        op.drop_constraint('fk_analysis_result_reviewed_by', 'analysis_result', type_='foreignkey')
        op.drop_constraint('fk_analysis_result_created_by', 'analysis_result', type_='foreignkey')
        op.drop_constraint('fk_analysis_result_sample', 'analysis_result', type_='foreignkey')
    except Exception:
        pass

    # Drop unique constraints
    try:
        op.drop_constraint('uq_equipment_code', 'equipment', type_='unique')
        op.drop_constraint('uq_user_username', 'user', type_='unique')
        op.drop_constraint('uq_sample_analysis', 'analysis_result', type_='unique')
        op.drop_constraint('uq_sample_code', 'sample', type_='unique')
    except Exception:
        pass
