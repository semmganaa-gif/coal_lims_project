"""bottle constants

Revision ID: 73d32cedfaa9
Revises: 29e2dc9228c9
Create Date: 2025-11-11 21:43:34.028509

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73d32cedfaa9'
down_revision = '29e2dc9228c9'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite: "1", PostgreSQL: "TRUE"
    bind = op.get_bind()
    bool_true = "1" if bind.dialect.name == "sqlite" else "TRUE"

    # --- bottle ---
    op.create_table(
        "bottle",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("serial_no", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=64)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text(bool_true)),
        sa.Column("created_by_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("serial_no", name="uq_bottle_serial_no"),
    )
    # индексүүдийг тусад нь
    op.create_index("ix_bottle_serial_no", "bottle", ["serial_no"], unique=False)

    # --- bottle_constant ---
    op.create_table(
        "bottle_constant",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bottle_id", sa.Integer(), sa.ForeignKey("bottle.id"), nullable=False, index=True),
        sa.Column("trial_1", sa.Float(), nullable=False),
        sa.Column("trial_2", sa.Float(), nullable=False),
        sa.Column("trial_3", sa.Float(), nullable=False),
        sa.Column("avg_value", sa.Float(), nullable=False),
        sa.Column("temperature_c", sa.Float(), nullable=False, server_default=sa.text("20")),
        sa.Column("effective_from", sa.DateTime(), nullable=False),
        sa.Column("effective_to", sa.DateTime()),
        sa.Column("remarks", sa.String(length=255)),
        sa.Column("approved_by_id", sa.Integer()),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column("created_by_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_bottle_constant_bottle", "bottle_constant", ["bottle_id"], unique=False)
    op.create_index("ix_bottle_constant_avg", "bottle_constant", ["avg_value"], unique=False)


def downgrade():
    # индексүүдээ эхлээд буулгаад, дараа нь хүснэгтээ устгана
    op.drop_index("ix_bottle_constant_avg", table_name="bottle_constant")
    op.drop_index("ix_bottle_constant_bottle", table_name="bottle_constant")
    op.drop_table("bottle_constant")

    op.drop_index("ix_bottle_serial_no", table_name="bottle")
    op.drop_table("bottle")
