"""Update client_name constraint for water sources

Revision ID: 202601300002
Revises: 202601300001
Create Date: 2026-01-30
"""
from alembic import op

revision = '202601300002'
down_revision = '202601300001'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old constraint and add new one with water source types
    with op.batch_alter_table('sample', schema=None) as batch_op:
        batch_op.drop_constraint('ck_sample_client_name', type_='check')
        batch_op.create_check_constraint(
            'ck_sample_client_name',
            "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB',"
            "'naimdain','maiga','tsagaan_khad','sum','uurhaichin','tsetsii',"
            "'gallerey','negdsen_office','uutsb','sbutsb','busad')"
        )


def downgrade():
    with op.batch_alter_table('sample', schema=None) as batch_op:
        batch_op.drop_constraint('ck_sample_client_name', type_='check')
        batch_op.create_check_constraint(
            'ck_sample_client_name',
            "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB')"
        )
