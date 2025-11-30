"""add_indices_client_name_sample_type

Revision ID: 00bedb0e989a
Revises: 8888c62ea786
Create Date: 2025-11-24 08:04:10.572799

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00bedb0e989a'
down_revision = '8888c62ea786'
branch_labels = None
depends_on = None


def upgrade():
    # Дээж хайлтын гүйцэтгэлийг сайжруулах индексүүд
    op.create_index('ix_sample_client_name', 'sample', ['client_name'])
    op.create_index('ix_sample_sample_type', 'sample', ['sample_type'])
    # Composite index - client_name, sample_type, status хослолоор хайх
    op.create_index('ix_sample_client_type_status', 'sample', ['client_name', 'sample_type', 'status'])


def downgrade():
    # Индексүүдийг устгах
    op.drop_index('ix_sample_client_type_status', table_name='sample')
    op.drop_index('ix_sample_sample_type', table_name='sample')
    op.drop_index('ix_sample_client_name', table_name='sample')
