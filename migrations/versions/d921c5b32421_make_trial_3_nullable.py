"""make trial_3 nullable

Revision ID: d921c5b32421
Revises: 73d32cedfaa9
Create Date: 2025-11-12 01:15:49.595940

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd921c5b32421'
down_revision = '73d32cedfaa9'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    check_name = 'ck_sample_client_name'
    new_expr = "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB')"

    if dialect == 'postgresql':
        # Check if constraint exists before dropping
        result = bind.execute(sa.text(
            "SELECT 1 FROM pg_constraint WHERE conname = :name"
        ), {"name": check_name}).fetchone()
        if result:
            op.drop_constraint(check_name, 'sample', type_='check')
        op.create_check_constraint(check_name, 'sample', new_expr)
    else:
        with op.batch_alter_table('sample', recreate='always') as batch:
            pass

    with op.batch_alter_table('bottle_constant', recreate='always') as batch:
        batch.alter_column(
            'trial_3',
            existing_type=sa.Float(),
            nullable=True
        )


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    check_name = 'ck_sample_client_name'
    old_expr = "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','LAB')"

    if dialect == 'postgresql':
        # Check if constraint exists before dropping
        result = bind.execute(sa.text(
            "SELECT 1 FROM pg_constraint WHERE conname = :name"
        ), {"name": check_name}).fetchone()
        if result:
            op.drop_constraint(check_name, 'sample', type_='check')
        op.create_check_constraint(check_name, 'sample', old_expr)
    else:
        with op.batch_alter_table('sample', recreate='always') as batch:
            pass

    with op.batch_alter_table('bottle_constant', recreate='always') as batch:
        batch.alter_column(
            'trial_3',
            existing_type=sa.Float(),
            nullable=False
        )
