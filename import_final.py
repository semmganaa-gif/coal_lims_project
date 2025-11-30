# import_final.py (FINAL VERSION WITH UNIQUE CONSTRAINT FIX)
import os
import pandas as pd
from app import create_app, db
from app.models import Equipment
from datetime import datetime, timedelta

# Flask app context үүсгэх
app = create_app()

def parse_date(date_val):
    """Огноог хөрвүүлэх"""
    if pd.isna(date_val) or str(date_val).strip() == "": return None
    try:
        if isinstance(date_val, datetime): return date_val.date()
        clean_str = str(date_val).replace('.', '-').replace('/', '-')[:10]
        return datetime.strptime(clean_str, "%Y-%m-%d").date()
    except: return None

def guess_category(name):
    """Нэрээр нь ангилал таах"""
    name = str(name).lower()
    if 'зуух' in name or 'furnace' in name: return 'furnace'
    if 'бутлуур' in name or 'тээрэм' in name or 'mill' in name or 'crusher' in name: return 'prep'
    if 'жин' in name or 'balance' in name or 'scale' in name: return 'balance'
    if 'анализатор' in name or 'илчлэг' in name or 'хүхэр' in name: return 'analysis'
    if 'ус' in name or 'water' in name or 'ph' in name: return 'water'
    if 'микро' in name or 'micro' in name or 'инкубатор' in name: return 'micro'
    return 'other' 

def run_import():
    file_name = 'Багаж ТТ-ийн нэгдсэн бүртгэл-2025.10.27.xlsx'

    if not os.path.exists(file_name):
        print(f"❌ АЛДАА: '{file_name}' файл олдохгүй байна!")
        return

    print(f"📂 Excel файлыг уншиж байна (2 дахь хуудас / Sheet Index 1)...")
    try:
        # ✅ 2-р хуудас (index 1). Толгой мөрийг Excel-ийн 5-р мөрнөөс (index 4) авна.
        # 4-р мөр нь асуудал үүсгээд байсан тул 5-р мөр рүү шилжүүллээ.
        df = pd.read_excel(file_name, sheet_name=1, header=0)
    except Exception as e:
        print(f"❌ Excel уншихад алдаа гарлаа: {e}")
        return
    
    # 2. Баганын нэрсийг цэвэрлэж, тааруулах
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]

    mapping = {
        'Багаж, тоног төхөөрөмжийн нэр': 'name', 
        'Үйлдвэрлэгчийн нэр': 'manufacturer', 
        'Марк, дугаар': 'model', 
        'Serial №': 'serial_number', 
        'Лабораторийн дугаар': 'lab_code',
        'Тоо хэмжээ': 'quantity', 
        'Байршил': 'location', 
        'Ашиглалтад орсон огноо': 'commissioned_info', 
        'Бусад тайлбар': 'remark',
        'Хэвийн (√)': 'is_normal',
        'Эвдрэлтэй (√)': 'is_broken',
    }
    cols_to_rename = {k: v for k, v in mapping.items() if k in df.columns}
    df.rename(columns=cols_to_rename, inplace=True)
    
    if 'name' not in df.columns:
        print("❌ АЛДАА: 'name' баганыг олохгүй байна! (Багаж, тоног төхөөрөмжийн нэр)")
        print(f"Уншсан бүх багана: {df.columns.tolist()}")
        return

    count = 0
    with app.app_context():
        # 3. Мөр бүрээр гүйж хадгалах
        for _, row in df.iterrows():
            if pd.isna(row.get('name')): continue

            # Status тохируулах
            status_val = 'normal'
            if row.get('is_broken') == '√':
                status_val = 'broken'
            
            # ✅ UNIQUE constraint-ийг засах: NaN бол None болгох
            raw_serial = row.get('serial_number')
            serial_number_val = str(raw_serial).strip() if pd.notna(raw_serial) else None
            
            # Lab Code-ийг None болгох
            raw_lab_code = row.get('lab_code')
            lab_code_val = str(raw_lab_code).strip() if pd.notna(raw_lab_code) else None


            eq = Equipment(
                name=str(row.get('name', '')),
                manufacturer=str(row.get('manufacturer', '') or ''),
                model=str(row.get('model', '') or ''),
                serial_number=serial_number_val, # ✅ Засварласан
                lab_code=lab_code_val,           # ✅ Засварласан
                quantity=int(row.get('quantity') or 1),
                location=str(row.get('location', '') or ''), 
                category=guess_category(row.get('name')),
                status=status_val,
                commissioned_info=str(row.get('commissioned_info', '') or ''),
                remark=str(row.get('remark', '') or '')
                # Бусад талбарууд (calibration date, cycle) энэ хуудаст байхгүй тул None байна
            )
            db.session.add(eq)
            count += 1

        db.session.commit()
        print(f"✅ АМЖИЛТТАЙ: Нийт {count} төхөөрөмж бааз руу орлоо!")

if __name__ == "__main__":
    run_import()