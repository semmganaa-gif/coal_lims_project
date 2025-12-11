"""Add audit log protection fields

Revision ID: 5a12246ee019
Revises: 6a4aab7bb1cf
Create Date: 2025-12-02 02:13:17.728329

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a12246ee019'
down_revision = '6a4aab7bb1cf'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite-д foreign key өөрчлөх нь төвөгтэй тул зөвхөн шинэ баганууд нэмнэ
    # CASCADE -> SET NULL өөрчлөлт нь application level дээр шийдэгдэнэ
    with op.batch_alter_table('analysis_result_log', schema=None) as batch_op:
        batch_op.add_column(sa.Column('original_user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('original_timestamp', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('sample_code_snapshot', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('data_hash', sa.String(length=64), nullable=True))
        # nullable=True болгох (sample/result устахад log үлдэх)
        batch_op.alter_column('sample_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('analysis_result_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade():
    with op.batch_alter_table('analysis_result_log', schema=None) as batch_op:
        batch_op.alter_column('analysis_result_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('sample_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.drop_column('data_hash')
        batch_op.drop_column('sample_code_snapshot')
        batch_op.drop_column('original_timestamp')
        batch_op.drop_column('original_user_id')
