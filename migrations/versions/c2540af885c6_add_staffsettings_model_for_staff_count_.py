"""Add StaffSettings model for staff count settings

Revision ID: c2540af885c6
Revises: 355b372934ee
Create Date: 2025-12-03 04:53:54.221429

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2540af885c6'
down_revision = '355b372934ee'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('staff_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('month', sa.Integer(), nullable=False),
    sa.Column('preparers', sa.Integer(), nullable=True),
    sa.Column('chemists', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('year', 'month', name='uq_staff_settings_month')
    )


def downgrade():
    op.drop_table('staff_settings')
