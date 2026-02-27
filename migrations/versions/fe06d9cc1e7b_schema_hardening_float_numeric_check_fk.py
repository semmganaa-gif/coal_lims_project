"""schema_hardening_float_numeric_check_fk

Revision ID: fe06d9cc1e7b
Revises: 53884d8642d7
Create Date: 2026-02-28 03:04:38.352560

Changes:
  - Float → Numeric(12,4): analysis_result.final_result, sample.weight
  - CHECK constraints: sample.status, analysis_result.status,
    equipment.status, chemical.status, corrective_action.status/severity
  - FK: sample.mass_ready_by_id → user.id
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe06d9cc1e7b'
down_revision = '53884d8642d7'
branch_labels = None
depends_on = None


def _pre_check_constraints(conn):
    """Verify no existing rows violate the new CHECK constraints."""
    checks = [
        (
            "sample",
            "status",
            "('new','in_progress','analysis','completed','archived')",
        ),
        (
            "analysis_result",
            "status",
            "('pending_review','approved','rejected','reanalysis')",
        ),
        (
            "equipment",
            "status",
            "('normal','maintenance','calibration','out_of_service','retired')",
        ),
        (
            "chemical",
            "status",
            "('active','low_stock','expired','empty','disposed')",
        ),
        (
            "corrective_action",
            "status",
            "('open','in_progress','reviewed','closed')",
        ),
        (
            "corrective_action",
            "severity",
            "('Critical','Major','Minor')",
        ),
    ]
    for table, column, values in checks:
        result = conn.execute(
            sa.text(
                f"SELECT COUNT(*) FROM {table} "
                f"WHERE {column} IS NOT NULL AND {column} NOT IN {values}"
            )
        )
        bad_count = result.scalar()
        if bad_count:
            raise RuntimeError(
                f"Pre-check FAILED: {table}.{column} has {bad_count} rows "
                f"with values not in {values}. Fix data before migrating."
            )

    # Verify mass_ready_by_id references valid users
    result = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM sample s "
            "WHERE s.mass_ready_by_id IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM \"user\" u WHERE u.id = s.mass_ready_by_id)"
        )
    )
    bad_count = result.scalar()
    if bad_count:
        raise RuntimeError(
            f"Pre-check FAILED: sample.mass_ready_by_id has {bad_count} rows "
            f"referencing non-existent user IDs. Fix data before migrating."
        )


def upgrade():
    conn = op.get_bind()
    _pre_check_constraints(conn)

    # --- 1. Float → Numeric(12,4) ---
    with op.batch_alter_table('analysis_result', schema=None) as batch_op:
        batch_op.alter_column(
            'final_result',
            existing_type=sa.DOUBLE_PRECISION(precision=53),
            type_=sa.Numeric(precision=12, scale=4),
            existing_nullable=True,
            postgresql_using='final_result::numeric(12,4)',
        )

    with op.batch_alter_table('sample', schema=None) as batch_op:
        batch_op.alter_column(
            'weight',
            existing_type=sa.DOUBLE_PRECISION(precision=53),
            type_=sa.Numeric(precision=12, scale=4),
            existing_nullable=True,
            postgresql_using='weight::numeric(12,4)',
        )

    # --- 2. CHECK constraints ---
    op.create_check_constraint(
        'ck_sample_status', 'sample',
        "status IN ('new','in_progress','analysis','completed','archived')",
    )
    op.create_check_constraint(
        'ck_analysis_result_status', 'analysis_result',
        "status IN ('pending_review','approved','rejected','reanalysis')",
    )
    op.create_check_constraint(
        'ck_equipment_status', 'equipment',
        "status IN ('normal','maintenance','calibration','out_of_service','retired')",
    )
    op.create_check_constraint(
        'ck_chemical_status', 'chemical',
        "status IN ('active','low_stock','expired','empty','disposed')",
    )
    op.create_check_constraint(
        'ck_corrective_action_status', 'corrective_action',
        "status IN ('open','in_progress','reviewed','closed')",
    )
    op.create_check_constraint(
        'ck_corrective_action_severity', 'corrective_action',
        "severity IN ('Critical','Major','Minor')",
    )

    # --- 3. Foreign key: sample.mass_ready_by_id → user.id ---
    with op.batch_alter_table('sample', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_sample_mass_ready_by_id', 'user',
            ['mass_ready_by_id'], ['id'],
        )


def downgrade():
    # --- 3. Drop FK ---
    with op.batch_alter_table('sample', schema=None) as batch_op:
        batch_op.drop_constraint('fk_sample_mass_ready_by_id', type_='foreignkey')

    # --- 2. Drop CHECK constraints ---
    op.drop_constraint('ck_corrective_action_severity', 'corrective_action', type_='check')
    op.drop_constraint('ck_corrective_action_status', 'corrective_action', type_='check')
    op.drop_constraint('ck_chemical_status', 'chemical', type_='check')
    op.drop_constraint('ck_equipment_status', 'equipment', type_='check')
    op.drop_constraint('ck_analysis_result_status', 'analysis_result', type_='check')
    op.drop_constraint('ck_sample_status', 'sample', type_='check')

    # --- 1. Numeric → Float ---
    with op.batch_alter_table('sample', schema=None) as batch_op:
        batch_op.alter_column(
            'weight',
            existing_type=sa.Numeric(precision=12, scale=4),
            type_=sa.DOUBLE_PRECISION(precision=53),
            existing_nullable=True,
            postgresql_using='weight::double precision',
        )

    with op.batch_alter_table('analysis_result', schema=None) as batch_op:
        batch_op.alter_column(
            'final_result',
            existing_type=sa.Numeric(precision=12, scale=4),
            type_=sa.DOUBLE_PRECISION(precision=53),
            existing_nullable=True,
            postgresql_using='final_result::double precision',
        )
