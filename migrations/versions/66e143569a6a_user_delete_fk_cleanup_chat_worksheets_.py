"""user delete FK cleanup — chat / worksheets / settings

Revision ID: 66e143569a6a
Revises: 45d7d1a997ca
Create Date: 2026-05-16 22:09:51.724944

Phase 2 Models M2-аас орхигдсон FK 6 ширхэгийг засна. User устгахад
FK violation үүсэхээс сэргийлнэ:

  - chat_messages.sender_id        : RESTRICT → CASCADE   (sender delete → msg delete)
  - chat_messages.receiver_id      : RESTRICT → SET NULL  (broadcast болно)
  - user_online_status.user_id (PK): RESTRICT → CASCADE
  - system_setting.updated_by_id   : RESTRICT → SET NULL
  - water_worksheet.analyst_id     : RESTRICT(NOT NULL) → SET NULL (nullable=True)
  - water_worksheet.reviewer_id    : RESTRICT → SET NULL
"""
from alembic import op
import sqlalchemy as sa


revision = '66e143569a6a'
down_revision = '45d7d1a997ca'
branch_labels = None
depends_on = None


def _replace_fk(table: str, name: str, column: str, ondelete: str) -> None:
    """FK constraint-ыг шинэ ondelete-той дахин үүсгэх."""
    op.drop_constraint(name, table, type_='foreignkey')
    op.create_foreign_key(
        name, table, 'user', [column], ['id'], ondelete=ondelete,
    )


def _revert_fk(table: str, name: str, column: str) -> None:
    """FK constraint-ыг ondelete-гүй (RESTRICT default) сэргээх."""
    op.drop_constraint(name, table, type_='foreignkey')
    op.create_foreign_key(name, table, 'user', [column], ['id'])


def upgrade():
    _replace_fk('chat_messages', 'chat_messages_sender_id_fkey', 'sender_id', 'CASCADE')
    _replace_fk('chat_messages', 'chat_messages_receiver_id_fkey', 'receiver_id', 'SET NULL')
    _replace_fk('user_online_status', 'user_online_status_user_id_fkey', 'user_id', 'CASCADE')
    _replace_fk('system_setting', 'system_setting_updated_by_id_fkey', 'updated_by_id', 'SET NULL')

    op.alter_column(
        'water_worksheet', 'analyst_id',
        existing_type=sa.Integer(), nullable=True,
    )
    _replace_fk('water_worksheet', 'water_worksheet_analyst_id_fkey', 'analyst_id', 'SET NULL')
    _replace_fk('water_worksheet', 'water_worksheet_reviewer_id_fkey', 'reviewer_id', 'SET NULL')


def downgrade():
    _revert_fk('water_worksheet', 'water_worksheet_reviewer_id_fkey', 'reviewer_id')
    _revert_fk('water_worksheet', 'water_worksheet_analyst_id_fkey', 'analyst_id')
    op.alter_column(
        'water_worksheet', 'analyst_id',
        existing_type=sa.Integer(), nullable=False,
    )
    _revert_fk('system_setting', 'system_setting_updated_by_id_fkey', 'updated_by_id')
    _revert_fk('user_online_status', 'user_online_status_user_id_fkey', 'user_id')
    _revert_fk('chat_messages', 'chat_messages_receiver_id_fkey', 'receiver_id')
    _revert_fk('chat_messages', 'chat_messages_sender_id_fkey', 'sender_id')
