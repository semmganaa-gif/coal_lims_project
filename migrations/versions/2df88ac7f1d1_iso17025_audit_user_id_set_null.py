"""ISO 17025: audit FK-уудад ondelete=SET NULL — immutable history хадгалах

Revision ID: 2df88ac7f1d1
Revises: c3d4e5f6a7b8
Create Date: 2026-05-15 17:59:22.390743

Audit мөрүүд (AuditLog, AnalysisResultLog) нь ISO 17025-ийн immutable
trail-ын суурь. User устсан үед history-ийг хадгалахын тулд:
- audit_log.user_id → ondelete=SET NULL
- analysis_result_log.user_id → ondelete=SET NULL + nullable
- analysis_result_log.original_user_id → ondelete=SET NULL

original_user_id нь "анхны хадгалсан химичийн ID-г үргэлж хадгалдаг"
тул түүний хувьд User устсан ч NULL утга үлдээж history-ийн контекст
бүрэн алдагдахаас сэргийлнэ.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2df88ac7f1d1'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('analysis_result_log', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.drop_constraint(batch_op.f('analysis_result_log_original_user_id_fkey'), type_='foreignkey')
        batch_op.drop_constraint(batch_op.f('analysis_result_log_user_id_fkey'), type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_analysis_result_log_user_id', 'user', ['user_id'], ['id'],
            ondelete='SET NULL',
        )
        batch_op.create_foreign_key(
            'fk_analysis_result_log_original_user_id', 'user', ['original_user_id'], ['id'],
            ondelete='SET NULL',
        )

    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('audit_log_user_id_fkey'), type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_audit_log_user_id', 'user', ['user_id'], ['id'],
            ondelete='SET NULL',
        )


def downgrade():
    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.drop_constraint('fk_audit_log_user_id', type_='foreignkey')
        batch_op.create_foreign_key(batch_op.f('audit_log_user_id_fkey'), 'user', ['user_id'], ['id'])

    with op.batch_alter_table('analysis_result_log', schema=None) as batch_op:
        batch_op.drop_constraint('fk_analysis_result_log_original_user_id', type_='foreignkey')
        batch_op.drop_constraint('fk_analysis_result_log_user_id', type_='foreignkey')
        batch_op.create_foreign_key(batch_op.f('analysis_result_log_user_id_fkey'), 'user', ['user_id'], ['id'])
        batch_op.create_foreign_key(batch_op.f('analysis_result_log_original_user_id_fkey'), 'user', ['original_user_id'], ['id'])
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
