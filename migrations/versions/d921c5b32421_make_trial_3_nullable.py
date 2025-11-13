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
    # 1) sample.client_name CHECK-г Proc багтаахаар шинэчлэх
    bind = op.get_bind()
    dialect = bind.dialect.name

    check_name = 'ck_sample_client_name'
    new_expr = "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB')"

    if dialect == 'postgresql':
        # PG дээр шууд drop/create хийе
        op.drop_constraint(check_name, 'sample', type_='check')
        op.create_check_constraint(check_name, 'sample', new_expr)
    else:
        # SQLite/MySQL-д найдвартай арга: recreate=always
        with op.batch_alter_table('sample', recreate='always') as batch:
            try:
                batch.drop_constraint(check_name, type_='check')
            except Exception:
                # зарим dialect дээр CHECK-н нэр байхгүй байж болно — алдаа үл тооё
                pass
            batch.create_check_constraint(check_name, new_expr)

    # 2) bottle_constant.trial_3 -> nullable=True
    with op.batch_alter_table('bottle_constant', recreate='always') as batch:
        batch.alter_column(
            'trial_3',
            existing_type=sa.Float(),
            nullable=True
        )


def downgrade():
    # 1) sample.client_name CHECK-ийг хуучин (Procгүй) нөлөөнд буцаах
    bind = op.get_bind()
    dialect = bind.dialect.name

    check_name = 'ck_sample_client_name'
    old_expr = "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','LAB')"

    if dialect == 'postgresql':
        op.drop_constraint(check_name, 'sample', type_='check')
        op.create_check_constraint(check_name, 'sample', old_expr)
    else:
        with op.batch_alter_table('sample', recreate='always') as batch:
            try:
                batch.drop_constraint(check_name, type_='check')
            except Exception:
                pass
            batch.create_check_constraint(check_name, old_expr)

    # 2) bottle_constant.trial_3-г буцаад NOT NULL болгох (шаардвал)
    with op.batch_alter_table('bottle_constant', recreate='always') as batch:
        batch.alter_column(
            'trial_3',
            existing_type=sa.Float(),
            nullable=False
        )
