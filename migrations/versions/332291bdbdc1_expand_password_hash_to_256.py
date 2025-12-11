"""expand_password_hash_to_256

Revision ID: 332291bdbdc1
Revises: 72440b447511
Create Date: 2025-12-11 13:51:53.328269

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '332291bdbdc1'
down_revision = '72440b447511'
branch_labels = None
depends_on = None


def upgrade():
    # password_hash баганыг 128 -> 256 болгох
    # scrypt hash 162 тэмдэгт байдаг тул 256 хангалттай
    op.alter_column(
        'user',
        'password_hash',
        type_=sa.String(256),
        existing_type=sa.String(128)
    )


def downgrade():
    op.alter_column(
        'user',
        'password_hash',
        type_=sa.String(128),
        existing_type=sa.String(256)
    )
