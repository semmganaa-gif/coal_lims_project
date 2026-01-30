# scripts/fix_audit_log_sequence.py
# -*- coding: utf-8 -*-
"""
PostgreSQL audit_log хүснэгтийн sequence-г засах.

Асуудал: SQLite-аас PostgreSQL руу migrate хийхэд sequence sync хийгдээгүй.
Шийдэл: Sequence-г хамгийн их id-аас дараагийн утга руу тохируулах.

Хэрэглээ:
    python scripts/fix_audit_log_sequence.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text


def fix_audit_log_sequence():
    """
    audit_log хүснэгтийн sequence-г засах.

    PostgreSQL-д sequence нь id багана дээр auto-increment утга үүсгэдэг.
    SQLite-аас migrate хийхэд sequence sync хийгдээгүй бол давхардсан key алдаа гарна.
    """
    app = create_app()

    with app.app_context():
        try:
            # 1. Одоогийн хамгийн их id-г олох
            result = db.session.execute(text("SELECT MAX(id) FROM audit_log"))
            max_id = result.scalar() or 0
            print(f"[INFO] audit_log хүснэгтийн хамгийн их id: {max_id}")

            # 2. Sequence нэрийг олох
            result = db.session.execute(text("""
                SELECT pg_get_serial_sequence('audit_log', 'id')
            """))
            sequence_name = result.scalar()

            if sequence_name:
                print(f"[INFO] Sequence нэр: {sequence_name}")

                # 3. Sequence-г max_id + 1 болгож тохируулах
                new_val = max_id + 1
                db.session.execute(text(f"SELECT setval('{sequence_name}', {new_val}, false)"))
                db.session.commit()

                print(f"[SUCCESS] Sequence-г {new_val} болгож тохируулсан.")

                # 4. Шалгах
                result = db.session.execute(text(f"SELECT last_value FROM {sequence_name}"))
                current_val = result.scalar()
                print(f"[VERIFY] Одоогийн sequence утга: {current_val}")
            else:
                # Sequence байхгүй бол шууд үүсгэх
                print("[WARNING] Sequence олдсонгүй. Шинээр үүсгэж байна...")

                # Create sequence
                db.session.execute(text(f"""
                    CREATE SEQUENCE IF NOT EXISTS audit_log_id_seq
                    START WITH {max_id + 1}
                    INCREMENT BY 1
                    NO MINVALUE
                    NO MAXVALUE
                    CACHE 1
                """))

                # Link sequence to column
                db.session.execute(text("""
                    ALTER TABLE audit_log
                    ALTER COLUMN id SET DEFAULT nextval('audit_log_id_seq')
                """))

                db.session.commit()
                print(f"[SUCCESS] Sequence үүсгэж, {max_id + 1}-ээс эхлүүлсэн.")

            # 5. Бусад хүснэгтүүдийн sequence-г шалгах
            tables_with_id = [
                'user', 'sample', 'analysis_result', 'equipment',
                'usage_log', 'system_setting', 'chat_message'
            ]

            print("\n[INFO] Бусад хүснэгтүүдийн sequence шалгаж байна...")
            for table in tables_with_id:
                try:
                    # Get max id
                    result = db.session.execute(text(f"SELECT MAX(id) FROM {table}"))
                    max_id = result.scalar() or 0

                    # Get sequence name
                    result = db.session.execute(text(f"""
                        SELECT pg_get_serial_sequence('{table}', 'id')
                    """))
                    seq_name = result.scalar()

                    if seq_name:
                        # Get current sequence value
                        result = db.session.execute(text(f"SELECT last_value FROM {seq_name}"))
                        seq_val = result.scalar()

                        if seq_val <= max_id:
                            # Fix sequence
                            new_val = max_id + 1
                            db.session.execute(text(f"SELECT setval('{seq_name}', {new_val}, false)"))
                            db.session.commit()
                            print(f"  [{table}] FIXED: {seq_val} -> {new_val}")
                        else:
                            print(f"  [{table}] OK (max_id={max_id}, seq={seq_val})")
                except Exception as e:
                    print(f"  [{table}] SKIP: {e}")

            print("\n[DONE] Sequence засвар дууслаа.")
            return True

        except Exception as e:
            print(f"[ERROR] Алдаа гарлаа: {e}")
            db.session.rollback()
            return False


if __name__ == "__main__":
    success = fix_audit_log_sequence()
    sys.exit(0 if success else 1)
