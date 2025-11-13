# upgrade_sqlite.py
#
# SQLite-д шинээр нэмсэн багануудыг гар аргаар ADD COLUMN хийх жижиг скрипт.
# Энэ скрипт 3 газар хайна:
#   1) ./app.db
#   2) ./lims.db
#   3) ./instance/app.db
# Олдсоныг нь нээгээд ALTER TABLE хийнэ.

import os
import sqlite3

# 1. аль DB байна гэдгийг олъё
CANDIDATES = [
    os.path.join(os.getcwd(), "app.db"),
    os.path.join(os.getcwd(), "lims.db"),
    os.path.join(os.getcwd(), "instance", "app.db"),
]

db_path = None
for p in CANDIDATES:
    if os.path.exists(p):
        db_path = p
        break

if not db_path:
    raise SystemExit("❌ SQLite файл олдсонгүй. app.db эсвэл lims.db чинь project дотор байна уу гэдгийг шалга.")

print(f"✅ Энэ DB дээр ажиллана: {db_path}")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

def try_alter(sql):
    try:
        print(f"→ {sql}")
        cur.execute(sql)
    except Exception as e:
        # аль хэдийн нэмэгдсэн/байгаа бол энд алгасна
        print(f"   ↳ алгаслаа: {e}")

# ----- 1. analysis_result хүснэгт -----
try_alter("ALTER TABLE analysis_result ADD COLUMN rejection_category VARCHAR(100);")
try_alter("ALTER TABLE analysis_result ADD COLUMN rejection_subcategory VARCHAR(100);")
try_alter("ALTER TABLE analysis_result ADD COLUMN rejection_comment VARCHAR(255);")

# ----- 2. analysis_result_log хүснэгт -----
try_alter("ALTER TABLE analysis_result_log ADD COLUMN rejection_category VARCHAR(100);")
try_alter("ALTER TABLE analysis_result_log ADD COLUMN rejection_subcategory VARCHAR(100);")

conn.commit()
conn.close()

print("🎉 Дууслаа. Одоо `python -X utf8 -m flask run` гээд серверээ асаагаарай.")
