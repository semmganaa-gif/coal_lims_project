# seed_equipment.py
"""
Excel-ээс тоног төхөөрөмжийн seed data үүсгэх.
Sheet "1" - Тоног төхөөрөмжийн нэгдсэн жагсаалт

Ажиллуулах:
    python seed_equipment.py
"""

import pandas as pd
from app import create_app, db
from app.models import Equipment

app = create_app()

EXCEL_FILE = r"D:\coal_lims_project\Copy of Багаж ТТ-ийн нэгдсэн бүртгэл-2025.12.07.xlsx"


def get_category(name, location):
    """Тоног төхөөрөмжийн нэрээр категори тодорхойлох."""
    name_lower = (name or '').lower()
    loc_lower = (location or '').lower()

    if 'зуух' in name_lower or 'муфел' in name_lower:
        return 'furnace'
    if 'бутлуур' in name_lower or 'тээрэм' in name_lower or 'сэгсрэгч' in name_lower:
        return 'prep'
    if 'жин' in name_lower:
        return 'balance'
    if 'хатаах' in name_lower:
        return 'dryer'
    if 'илчлэг' in name_lower or 'калоримет' in name_lower:
        return 'calorimeter'
    if 'хүхэр' in name_lower or 'sulfur' in name_lower:
        return 'sulfur'
    if 'хөөлт' in name_lower or 'csi' in name_lower or 'gi' in name_lower:
        return 'csi'
    if 'микро' in loc_lower or 'биолог' in loc_lower:
        return 'micro'
    if 'ус' in loc_lower or 'water' in name_lower:
        return 'water'
    if 'wtl' in loc_lower or 'бсл' in loc_lower:
        return 'wtl'
    if 'xrf' in name_lower or 'фосфор' in name_lower:
        return 'analysis'
    if 'спектр' in name_lower or 'icp' in name_lower:
        return 'analysis'

    return 'other'


def get_status(remark):
    """Тайлбараас status тодорхойлох."""
    remark_lower = (remark or '').lower()

    if 'засвар' in remark_lower:
        return 'maintenance'
    if 'контейнер' in remark_lower or 'агуулах' in remark_lower:
        return 'retired'  # Ашиглахгүй байгаа
    return 'normal'


def seed_equipment():
    """Excel-ээс тоног төхөөрөмж seed хийх."""

    print("=" * 70)
    print("ТОНОГ ТӨХӨӨРӨМЖИЙН SEED")
    print("=" * 70)

    # Excel унших
    df = pd.read_excel(EXCEL_FILE, sheet_name='1', header=None)
    print(f"Excel уншлаа: {len(df)} мөр")

    created_count = 0
    skipped_count = 0

    for idx, row in df.iterrows():
        # Толгой мөрүүдийг алгасах
        first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''

        # Тоо биш бол алгасах
        try:
            int(float(first_col))
        except ValueError:
            continue

        # Өгөгдөл авах
        name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
        manufacturer = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else None
        model = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else None
        serial_number = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else None
        lab_code = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else None
        location = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else None
        # row.iloc[7] = Шалгалт тохируулга
        quantity = 1
        try:
            quantity = int(float(row.iloc[8])) if pd.notna(row.iloc[8]) else 1
        except:
            pass
        manufactured_info = str(row.iloc[9]) if pd.notna(row.iloc[9]) else None
        commissioned_info = str(row.iloc[10]) if pd.notna(row.iloc[10]) else None
        remark = str(row.iloc[13]).strip() if pd.notna(row.iloc[13]) else None

        # Хоосон нэр бол алгасах
        if not name or name == 'NaN':
            continue

        # NaN цэвэрлэх
        if manufacturer == 'NaN':
            manufacturer = None
        if model == 'NaN' or model == '-':
            model = None
        if serial_number == 'NaN' or serial_number == '-':
            serial_number = None
        if lab_code == 'NaN' or lab_code == '-':
            lab_code = None
        if location == 'NaN':
            location = None
        if remark == 'NaN':
            remark = None

        # Давхардал шалгах (нэр + model + serial)
        existing = Equipment.query.filter_by(
            name=name, model=model
        ).first()

        if existing:
            skipped_count += 1
            continue

        # Category, status
        category = get_category(name, location)
        status = get_status(remark)

        # Equipment үүсгэх
        eq = Equipment(
            name=name,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            lab_code=lab_code,
            location=location,
            quantity=quantity,
            category=category,
            status=status,
            manufactured_info=manufactured_info,
            commissioned_info=commissioned_info,
            remark=remark,
        )
        db.session.add(eq)
        created_count += 1

        cat_short = category[:8] if category else '-'
        print(f"  + {name[:35]:<35} | {cat_short:<10} | {status}")

    db.session.commit()

    print("-" * 70)
    print(f"Шинээр үүсгэсэн: {created_count}")
    print(f"Давхардсан: {skipped_count}")
    print(f"Нийт Equipment: {Equipment.query.count()}")

    # Категори статистик
    print("\nКатегори тоо:")
    from sqlalchemy import func
    stats = db.session.query(
        Equipment.category, func.count(Equipment.id)
    ).group_by(Equipment.category).all()

    for cat, cnt in sorted(stats, key=lambda x: -x[1]):
        print(f"  {cat or 'None':<15} : {cnt}")

    print("=" * 70)


if __name__ == '__main__':
    with app.app_context():
        seed_equipment()
