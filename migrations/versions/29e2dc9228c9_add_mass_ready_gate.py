from alembic import op
import sqlalchemy as sa

# --- Alembic identifiers ---
revision = "29e2dc9228c9"
down_revision = "4409203ebf97"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    is_sqlite = bind.dialect.name == "sqlite"

    # 🧹 SQLite batch-ээс үлдэж магадгүй түр хүснэгтүүдийг цэвэрлэе
    if is_sqlite:
        op.execute("DROP TABLE IF EXISTS _alembic_tmp_sample")
        op.execute("DROP TABLE IF EXISTS alembic_tmp_sample")  # зарим хувилбарт нэр нь ийм байдаг

    existing_cols = {c["name"] for c in insp.get_columns("sample")}

    with op.batch_alter_table("sample") as batch:
        if "mass_ready" not in existing_cols:
            # SQLite: "0", PostgreSQL: "FALSE"
            default_val = "0" if is_sqlite else "FALSE"
            batch.add_column(
                sa.Column("mass_ready", sa.Boolean(), nullable=False, server_default=sa.text(default_val))
            )
        if "mass_ready_at" not in existing_cols:
            batch.add_column(sa.Column("mass_ready_at", sa.DateTime(), nullable=True))
        if "mass_ready_by_id" not in existing_cols:
            batch.add_column(sa.Column("mass_ready_by_id", sa.Integer(), nullable=True))

    # Индексийг IF NOT EXISTS-тай хийх (Alembic helper нь IF NOT EXISTSгүй)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sample_mass_ready ON sample (mass_ready)")

    # ⛔ SQLite: DROP DEFAULT дэмждэггүй. Иймд бусад СУБД дээр л default-ийг авна.
    if not is_sqlite:
        op.alter_column("sample", "mass_ready", server_default=None)


def downgrade():
    # Индексийг эхлээд устгана
    # Alembic helper хэрэглэвэл 'IF EXISTS' байхгүй тул plain SQL ашиглав.
    op.execute("DROP INDEX IF EXISTS ix_sample_mass_ready")

    # Багануудыг буцаах (байгааг нь шалгаад унагаах нь SQLite дээр batch mode-д OK)
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_cols = {c["name"] for c in insp.get_columns("sample")}

    with op.batch_alter_table("sample") as batch:
        if "mass_ready_by_id" in existing_cols:
            batch.drop_column("mass_ready_by_id")
        if "mass_ready_at" in existing_cols:
            batch.drop_column("mass_ready_at")
        if "mass_ready" in existing_cols:
            batch.drop_column("mass_ready")