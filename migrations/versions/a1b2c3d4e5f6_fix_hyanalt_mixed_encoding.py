"""Fix hyanalт mixed Latin+Cyrillic encoding → hyanalt (audit H2).

`'hyanalт'` нь Latin "hyanal" + Cyrillic "т" (U+0442) холимог тэмдэгт байсан.
Бусад client_name утгууд бүгд Latin transliteration (uutsb, negdsen_office,
tsagaan_khad гэх мэт) тул `'hyanalt'` (Latin) болгож нэгтгэв.

Үйлдэл:
  1. UPDATE sample SET client_name = 'hyanalt' WHERE client_name = 'hyanalт'
  2. CHECK constraint солих (хуучин дотор 'hyanalт', шинэ дотор 'hyanalt')

Revision ID: a1b2c3d4e5f6
Revises: 23d3a3d7c5a3
Create Date: 2026-05-14 10:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '23d3a3d7c5a3'
branch_labels = None
depends_on = None


# Шинэ зөв жагсаалт (бусад утгууд хэвээр, зөвхөн hyanalт → hyanalt)
_NEW_CLIENT_NAMES = (
    "'CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB',"
    "'uutsb','negdsen_office','tsagaan_khad','tsetsii',"
    "'naymant','naimdai','malchdyn_hudag',"
    "'hyanalt','tsf','uarp','shine_camp','busad',"
    "'dotood_air','dotood_swab',"
    "'naimdain','maiga','sum','uurhaichin','gallerey','sbutsb'"
)
_OLD_CLIENT_NAMES = (
    "'CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB',"
    "'uutsb','negdsen_office','tsagaan_khad','tsetsii',"
    "'naymant','naimdai','malchdyn_hudag',"
    "'hyanalт','tsf','uarp','shine_camp','busad',"  # ← buggy mixed encoding
    "'dotood_air','dotood_swab',"
    "'naimdain','maiga','sum','uurhaichin','gallerey','sbutsb'"
)


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name

    # 1) Хуучин буруу encoding-той row-уудыг шинэчлэх (DB-д орсон байж магадгүй).
    result = conn.execute(
        sa.text("UPDATE sample SET client_name = 'hyanalt' WHERE client_name = 'hyanalт'")
    )
    if result.rowcount:
        print(f"[a1b2c3d4e5f6] Migrated {result.rowcount} sample rows: 'hyanalт' → 'hyanalt'")

    # 2) CHECK constraint солих. SQLite-д batch mode ашиглана.
    if dialect == 'sqlite':
        with op.batch_alter_table('sample') as batch_op:
            batch_op.drop_constraint('ck_sample_client_name', type_='check')
            batch_op.create_check_constraint(
                'ck_sample_client_name',
                f"client_name IN ({_NEW_CLIENT_NAMES})",
            )
    else:
        op.drop_constraint('ck_sample_client_name', 'sample', type_='check')
        op.create_check_constraint(
            'ck_sample_client_name',
            'sample',
            f"client_name IN ({_NEW_CLIENT_NAMES})",
        )


def downgrade():
    """Сэргээх: зөвлөмж хийхгүй (encoding bug-руу буцах нь зөв биш)."""
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'sqlite':
        with op.batch_alter_table('sample') as batch_op:
            batch_op.drop_constraint('ck_sample_client_name', type_='check')
            batch_op.create_check_constraint(
                'ck_sample_client_name',
                f"client_name IN ({_OLD_CLIENT_NAMES})",
            )
    else:
        op.drop_constraint('ck_sample_client_name', 'sample', type_='check')
        op.create_check_constraint(
            'ck_sample_client_name',
            'sample',
            f"client_name IN ({_OLD_CLIENT_NAMES})",
        )

    # downgrade-д hyanalt → hyanalт сэргээх нь bug сэргээнэ — зүгээр зөвлөмж бичнэ
    print("[a1b2c3d4e5f6] downgrade: rows-ийг сэргээхгүй (hyanalt-ыг хадгална).")
