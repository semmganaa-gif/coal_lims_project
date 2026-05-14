"""5 model-д ISO 17025 audit hash column нэмэх (audit H3).

MaintenanceLog, UsageLog, EnvironmentalLog, QCControlChart, ProficiencyTest нь
бүгд ISO 17025 audit trail-ийн дагуу immutable байх ёстой records. Өмнө нь
HashableMixin + event.listen хамгаалалт байхгүй байсныг засаж data_hash column
+ append-only event listeners нэмсэн (model түвшинд).

Хүснэгт бүрд `data_hash VARCHAR(64) NULLABLE` column нэмэв. NULL зөвшөөрсөн нь
existing rows-ыг хадгалахын тулд (backfill optional).

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-14 10:45:00
"""
from alembic import op
import sqlalchemy as sa


revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


_TABLES = [
    'maintenance_logs',
    'usage_logs',
    'environmental_log',
    'qc_control_chart',
    'proficiency_test',
]


def upgrade():
    for table in _TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(
                sa.Column('data_hash', sa.String(length=64), nullable=True)
            )


def downgrade():
    for table in reversed(_TABLES):
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column('data_hash')
