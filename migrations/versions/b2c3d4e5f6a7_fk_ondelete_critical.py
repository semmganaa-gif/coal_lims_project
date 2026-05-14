"""FK ondelete behavior нэмэх — 4 critical FK (audit M2).

CLAUDE.md-д заасан Routes → Service → Repository → Model давхаргын дагуу,
FK-уудад DB-level ondelete behavior нэмж orphan-аас сэргийлэв. ORM cascade
relationship тохиргоо нь зөвхөн ORM-level — raw SQL DELETE-аас хамгаалдаггүй.

Засагдсан 4 FK:
  - sample.user_id → user.id ON DELETE SET NULL (audit retention)
  - sample.mass_ready_by_id → user.id ON DELETE SET NULL
  - analysis_result.sample_id → sample.id ON DELETE CASCADE (ORM cascade-тэй sync)
  - analysis_result.user_id → user.id ON DELETE SET NULL
  - chemical_usage.chemical_id → chemical.id ON DELETE CASCADE

Үлдсэн FK-уудыг (~10+) Phase 3-д шилжүүлсэн.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-14 10:30:00
"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def _recreate_fk(table: str, column: str, ref_table: str, ondelete: str,
                 fk_name: str | None = None) -> None:
    """SQLite/PostgreSQL хоёуланд ажиллах FK alter helper.

    SQLite ALTER FK дэмждэггүй тул batch_alter_table-аар хүснэгтийг recreate
    хийнэ. PostgreSQL шууд DROP+ADD.
    """
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'sqlite':
        with op.batch_alter_table(table) as batch_op:
            if fk_name:
                batch_op.drop_constraint(fk_name, type_='foreignkey')
            batch_op.create_foreign_key(
                fk_name or f"fk_{table}_{column}_{ref_table}",
                ref_table,
                [column],
                ['id'],
                ondelete=ondelete,
            )
    else:
        # PostgreSQL: FK-уудын нэр Alembic auto-generated байж магадгүй —
        # information_schema-аас хайж drop хийнэ.
        if fk_name:
            op.drop_constraint(fk_name, table, type_='foreignkey')
        else:
            # Find FK name dynamically
            result = conn.execute(sa.text("""
                SELECT constraint_name FROM information_schema.referential_constraints rc
                JOIN information_schema.key_column_usage kcu
                  ON rc.constraint_name = kcu.constraint_name
                WHERE kcu.table_name = :table AND kcu.column_name = :column
            """), {"table": table, "column": column}).first()
            if result:
                op.drop_constraint(result[0], table, type_='foreignkey')
        op.create_foreign_key(
            fk_name or f"fk_{table}_{column}_{ref_table}",
            table,
            ref_table,
            [column],
            ['id'],
            ondelete=ondelete,
        )


def upgrade():
    # 1) sample.user_id → SET NULL (audit retention)
    _recreate_fk('sample', 'user_id', 'user', 'SET NULL', fk_name='fk_sample_user_id')

    # 2) sample.mass_ready_by_id → SET NULL
    _recreate_fk('sample', 'mass_ready_by_id', 'user', 'SET NULL',
                 fk_name='fk_sample_mass_ready_by_id')

    # 3) analysis_result.sample_id → CASCADE
    _recreate_fk('analysis_result', 'sample_id', 'sample', 'CASCADE')

    # 4) analysis_result.user_id → SET NULL
    _recreate_fk('analysis_result', 'user_id', 'user', 'SET NULL')

    # 5) chemical_usage.chemical_id → CASCADE
    _recreate_fk('chemical_usage', 'chemical_id', 'chemical', 'CASCADE')


def downgrade():
    # Сэргээх: ondelete-гүй болгож буцаах
    _recreate_fk('sample', 'user_id', 'user', None, fk_name='fk_sample_user_id')
    _recreate_fk('sample', 'mass_ready_by_id', 'user', None,
                 fk_name='fk_sample_mass_ready_by_id')
    _recreate_fk('analysis_result', 'sample_id', 'sample', None)
    _recreate_fk('analysis_result', 'user_id', 'user', None)
    _recreate_fk('chemical_usage', 'chemical_id', 'chemical', None)
