"""equipment status add needs_spare

Revision ID: 45d7d1a997ca
Revises: 69695d8ac4e9
Create Date: 2026-05-16 20:51:31.414943

CheckConstraint-д needs_spare статус нэмэх. EquipmentStatus enum-ийн
lifecycle-ийг сэргээх (degraded operation, awaiting spare parts).

Note: Прод data-д 'broken' статус хадгалагдсан байж болзошгүй (UI-аас
DB-руу ороогүй CheckConstraint-ын улмаас) — тэдгээрийг 'out_of_service'-руу
backfill хийнэ.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '45d7d1a997ca'
down_revision = '69695d8ac4e9'
branch_labels = None
depends_on = None


def upgrade():
    # Backfill: 'broken' (хуучин UI value, CheckConstraint-аар реждектэгдэх
    # ёстой байсан ч migrate-ийн өмнө орсон бол) → 'out_of_service'
    op.execute(
        "UPDATE equipment SET status = 'out_of_service' WHERE status = 'broken'"
    )

    op.drop_constraint('ck_equipment_status', 'equipment', type_='check')
    op.create_check_constraint(
        'ck_equipment_status', 'equipment',
        "status IN ('normal','maintenance','calibration','needs_spare',"
        "'out_of_service','retired')",
    )


def downgrade():
    # needs_spare статустай equipment-уудыг буцаахдаа maintenance-руу (хамгийн ойр)
    op.execute(
        "UPDATE equipment SET status = 'maintenance' WHERE status = 'needs_spare'"
    )

    op.drop_constraint('ck_equipment_status', 'equipment', type_='check')
    op.create_check_constraint(
        'ck_equipment_status', 'equipment',
        "status IN ('normal','maintenance','calibration','out_of_service','retired')",
    )
