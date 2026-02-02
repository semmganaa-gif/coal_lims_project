"""Add chem_lab_id and micro_lab_id columns to sample

Revision ID: 202602030001
Revises: bf2ed60971e9
Create Date: 2026-02-03

"""
import re
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '202602030001'
down_revision = 'bf2ed60971e9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sample', sa.Column('chem_lab_id', sa.String(20), nullable=True))
    op.add_column('sample', sa.Column('micro_lab_id', sa.String(20), nullable=True))
    op.create_index('ix_sample_chem_lab_id', 'sample', ['chem_lab_id'])
    op.create_index('ix_sample_micro_lab_id', 'sample', ['micro_lab_id'])

    # Backfill: одоо байгаа дээжүүдийн sample_code-оос micro_lab_id задлах
    conn = op.get_bind()
    samples = conn.execute(
        sa.text(
            "SELECT id, sample_code, lab_type FROM sample "
            "WHERE lab_type IN ('microbiology', 'water & micro')"
        )
    ).fetchall()

    pattern = re.compile(r'^(\d{2}_\d{2})_(.+)_(\d{4}-\d{2}-\d{2})$')
    for row in samples:
        m = pattern.match(row[1])
        if m:
            lab_id = m.group(1)
            conn.execute(
                sa.text("UPDATE sample SET micro_lab_id = :lid WHERE id = :sid"),
                {'lid': lab_id, 'sid': row[0]},
            )


def downgrade():
    op.drop_index('ix_sample_micro_lab_id', 'sample')
    op.drop_index('ix_sample_chem_lab_id', 'sample')
    op.drop_column('sample', 'micro_lab_id')
    op.drop_column('sample', 'chem_lab_id')
