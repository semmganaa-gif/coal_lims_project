# seed_spare_parts.py
"""
Excel-ээс сэлбэг хэрэгслийн seed data үүсгэх.
Sheet "10" - Сэлбэг хэрэгслийн бүртгэл

Ажиллуулах:
    python seed_spare_parts.py
"""

import pandas as pd
import re
from app import create_app, db
from app.models import SparePart, SparePartLog, Equipment

app = create_app()

EXCEL_FILE = r"D:\coal_lims_project\Copy of Багаж ТТ-ийн нэгдсэн бүртгэл-2025.12.07.xlsx"


def parse_quantity(val):
    """Тоо хэмжээг parse хийх."""
    if pd.isna(val) or val is None:
        return 0

    val_str = str(val).strip()

    # Хоосон
    if not val_str or val_str == 'NaN':
        return 0

    # Тоо байвал шууд буцаах
    try:
        return float(val_str)
    except ValueError:
        pass

    # "2 хайрцаг", "34 боодол" гэх мэт
    match = re.search(r'(\d+)', val_str)
    if match:
        return float(match.group(1))

    return 0


def parse_usage_life(val):
    """Ашиглалтын хугацаа (сар) parse хийх."""
    if pd.isna(val) or val is None:
        return None

    val_str = str(val).strip()
    if not val_str or val_str == 'NaN':
        return None

    try:
        return int(float(val_str))
    except ValueError:
        return None


def get_category(equipment_name, spare_name):
    """Категори тодорхойлох."""
    name_lower = (spare_name or '').lower()

    if 'шүүлтүүр' in name_lower or 'filter' in name_lower or 'пильтер' in name_lower:
        return 'filter'
    if 'бүс' in name_lower or 'belt' in name_lower or 'оосор' in name_lower:
        return 'belt'
    if 'гэрэл' in name_lower or 'lamp' in name_lower or 'чийдэн' in name_lower:
        return 'lamp'
    if 'гал хамг' in name_lower or 'fuse' in name_lower or 'breaker' in name_lower or 'пускат' in name_lower:
        return 'fuse'
    if 'холхивч' in name_lower or 'bearing' in name_lower:
        return 'bearing'
    if 'битүүмж' in name_lower or 'seal' in name_lower or 'о-цагираг' in name_lower or 'o-ring' in name_lower or 'жийргэвч' in name_lower or 'резин' in name_lower:
        return 'seal'
    if 'хоолой' in name_lower or 'tube' in name_lower:
        return 'tube'
    if 'мэдрэгч' in name_lower or 'sensor' in name_lower or 'термопар' in name_lower or 'thermocouple' in name_lower:
        return 'sensor'
    if 'тигел' in name_lower or 'crucible' in name_lower or 'crusible' in name_lower:
        return 'other'  # Тигель - бусад

    return 'general'


def seed_spare_parts():
    """Excel-ээс сэлбэг хэрэгсэл seed хийх."""

    print("=" * 60)
    print("СЭЛБЭГ ХЭРЭГСЛИЙН SEED")
    print("=" * 60)

    # Excel унших
    df = pd.read_excel(EXCEL_FILE, sheet_name='10')
    print(f"Excel уншлаа: {len(df)} мөр")

    # Одоо байгаа Equipment-үүдийг авах (холбохын тулд)
    equipments = {eq.name.lower(): eq for eq in Equipment.query.all()}
    print(f"Тоног төхөөрөмж: {len(equipments)}")

    created_count = 0
    skipped_count = 0
    current_equipment = None

    for idx, row in df.iterrows():
        # Толгой мөрүүдийг алгасах
        first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''

        # "Тоног төхөөрөмжийн нэр" эсвэл "СЭЛБЭГ" гэсэн мөр бол алгасах
        if 'тоног төхөөрөмж' in first_col.lower() or 'сэлбэг' in first_col.lower():
            continue

        # Д/д багана (first_col) тоо биш бол алгасах
        if not first_col or first_col == 'Д/д' or first_col == 'NaN':
            continue

        try:
            int(float(first_col))  # Д/д тоо эсэх
        except ValueError:
            continue

        # Өгөгдөл авах
        equipment_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
        spare_name = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
        name_en = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ''
        # row.iloc[4] = Зураг (алгасах)
        quantity = parse_quantity(row.iloc[5])
        # row.iloc[6] = Шинээр ирсэн (алгасах)
        usage_life = parse_usage_life(row.iloc[7])

        # Хоосон нэр бол алгасах
        if not spare_name or spare_name == 'NaN':
            continue

        # Тоног төхөөрөмжийн нэр шинэчлэх
        if equipment_name and equipment_name != 'NaN':
            current_equipment = equipment_name

        # name_en цэвэрлэх
        if name_en == 'NaN':
            name_en = None

        # Давхардал шалгах
        existing = SparePart.query.filter_by(name=spare_name).first()
        if existing:
            # Давхардсан бол quantity нэмэх
            existing.quantity += quantity
            existing.update_status()
            skipped_count += 1
            continue

        # Equipment холбоос хайх
        equipment_id = None
        if current_equipment:
            # Төхөөрөмжийн нэрээр хайх
            for eq_name, eq in equipments.items():
                if eq_name in current_equipment.lower() or current_equipment.lower() in eq_name:
                    equipment_id = eq.id
                    break

        # Категори тодорхойлох
        category = get_category(current_equipment, spare_name)

        # SparePart үүсгэх
        spare_part = SparePart(
            name=spare_name,
            name_en=name_en,
            quantity=quantity,
            unit='pcs',
            reorder_level=max(1, quantity * 0.2),  # 20% reorder level
            compatible_equipment=current_equipment,
            equipment_id=equipment_id,
            usage_life_months=usage_life,
            category=category,
            status='active',
        )
        spare_part.update_status()

        db.session.add(spare_part)
        db.session.flush()

        # Аудит лог
        log = SparePartLog(
            spare_part_id=spare_part.id,
            action='created',
            quantity_change=quantity,
            quantity_before=0,
            quantity_after=quantity,
            user_id=1,  # Admin
            details=f"Excel seed: {current_equipment}"
        )
        db.session.add(log)

        created_count += 1
        print(f"  + {spare_name[:40]:<40} qty={quantity:<6} cat={category}")

    db.session.commit()

    print("-" * 60)
    print(f"Шинээр үүсгэсэн: {created_count}")
    print(f"Давхардсан (quantity нэмсэн): {skipped_count}")
    print(f"Нийт SparePart: {SparePart.query.count()}")
    print("=" * 60)


if __name__ == '__main__':
    with app.app_context():
        seed_spare_parts()
