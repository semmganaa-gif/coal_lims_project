"""Update client_name constraint for new water units

Revision ID: 202602030002
Revises: 202602030001
Create Date: 2026-02-03

"""
from alembic import op

revision = '202602030002'
down_revision = '202602030001'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_sample_client_name', 'sample', type_='check')
    op.create_check_constraint(
        'ck_sample_client_name',
        'sample',
        "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB',"
        "'uutsb','negdsen_office','tsagaan_khad','tsetsii',"
        "'naymant','naimdai','malchdyn_hudag',"
        "'hyanalт','tsf','uarp','shine_camp','busad',"
        "'dotood_air','dotood_swab',"
        "'naimdain','maiga','sum','uurhaichin','gallerey','sbutsb')",
    )


def downgrade():
    op.drop_constraint('ck_sample_client_name', 'sample', type_='check')
    op.create_check_constraint(
        'ck_sample_client_name',
        'sample',
        "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB',"
        "'naimdain','maiga','tsagaan_khad','sum','uurhaichin','tsetsii',"
        "'gallerey','negdsen_office','uutsb','sbutsb','busad',"
        "'dotood_air','dotood_swab')",
    )
