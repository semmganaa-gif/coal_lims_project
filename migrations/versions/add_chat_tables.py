"""Add chat tables for real-time messaging

Revision ID: add_chat_tables
Revises:
Create Date: 2024-12-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_chat_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Chat Messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('receiver_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('message_type', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['receiver_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_receiver_id'), 'chat_messages', ['receiver_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_sender_id'), 'chat_messages', ['sender_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_sent_at'), 'chat_messages', ['sent_at'], unique=False)

    # User Online Status table
    op.create_table('user_online_status',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_online', sa.Boolean(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('socket_id', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id')
    )


def downgrade():
    op.drop_table('user_online_status')
    op.drop_index(op.f('ix_chat_messages_sent_at'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_sender_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_receiver_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
