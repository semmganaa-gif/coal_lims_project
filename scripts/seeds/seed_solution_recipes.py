# seed_solution_recipes.py
# -*- coding: utf-8 -*-
"""
Уусмалын жорын seed script - Excel файлаас уншиж database-д нэмнэ.
Usage: flask shell < seed_solution_recipes.py
  эсвэл: python seed_solution_recipes.py
"""

import pandas as pd
import re
from app import create_app, db
from app.models import SolutionRecipe

# Excel файлаас өгөгдөл унших
EXCEL_FILE = 'Copy of Химийн бодисын урвалж найруулалт_титр тогтоох_бодисын зарцуулалт, устгал бүртгэлийн дэвтэр_2026.xlsx'

def parse_concentration(conc_str):
    """Концентрацийн утга болон нэгжийг салгах."""
    if not conc_str or pd.isna(conc_str) or conc_str == '-':
        return None, None

    conc_str = str(conc_str).strip()

    # Patterns
    patterns = [
        (r'^([\d.]+)\s*ммоль/л$', 'mmol/L'),
        (r'^([\d.]+)\s*моль/л$', 'mol/L'),
        (r'^([\d.]+)\s*мг/л$', 'mg/L'),
        (r'^([\d.]+)\s*г/л$', 'g/L'),
        (r'^([\d.]+)\s*µS/cm$', 'µS/cm'),
        (r'^([\d.]+)\s*ppm$', 'ppm'),
        (r'^([\d.]+)\s*мгN/л$', 'mgN/L'),
        (r'^([\d.]+)\s*N$', 'N'),
        (r'^([\d.]+)\s*%$', '%'),
        (r'^([\d.]+)$', ''),  # number only
        (r'^([\d.:]+)$', ''),  # ratio like 1:1
    ]

    for pattern, unit in patterns:
        match = re.match(pattern, conc_str, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1).replace(':', '.'))
                return val, unit or 'N'
            except:
                pass

    # Can't parse - truncate to 20 chars max (database limit)
    if len(conc_str) > 20:
        return None, None  # Too long, skip concentration
    return None, conc_str


def seed_recipes():
    """Excel файлаас уусмалын жор уншиж database-д нэмэх."""

    app = create_app()
    with app.app_context():
        # Excel унших
        df = pd.read_excel(EXCEL_FILE, sheet_name='Уусмал бэлдэх явц', header=None)

        # Өмнөх recipes устгах (шинээр нэмэх)
        existing_count = SolutionRecipe.query.filter_by(lab_type='water').count()
        if existing_count > 0:
            print(f"Анхааруулга: {existing_count} жор аль хэдийн байна.")
            user_input = input("Устгаад шинээр нэмэх үү? (y/n): ")
            if user_input.lower() == 'y':
                SolutionRecipe.query.filter_by(lab_type='water').delete()
                db.session.commit()
                print("Хуучин жорууд устгагдлаа.")
            else:
                print("Цуцаллаа.")
                return

        added = 0
        skipped = 0

        for idx, row in df.iterrows():
            # Skip header rows and empty rows
            num = row[0]
            if pd.isna(num) or not str(num).isdigit():
                continue

            name = row[2]  # Уусмалын нэр
            conc_str = row[3]  # Концентраци
            notes = row[4]  # Бэлдэх явц
            method = row[1]  # Стандарт аргачлал

            if pd.isna(name) or not name:
                continue

            name = str(name).strip()

            # Check if already exists
            existing = SolutionRecipe.query.filter_by(name=name, lab_type='water').first()
            if existing:
                skipped += 1
                continue

            # Parse concentration
            conc_val, conc_unit = parse_concentration(conc_str)

            # Preparation notes
            prep_notes = ''
            if not pd.isna(notes):
                prep_notes = str(notes).strip()

            # Add method info to notes
            if not pd.isna(method) and method:
                prep_notes = f"Стандарт: {method}\n\n{prep_notes}"

            # Determine category
            category = 'reagent'
            name_lower = name.lower()
            if 'буфер' in name_lower:
                category = 'buffer'
            elif 'индикатор' in name_lower:
                category = 'indicator'
            elif 'стандарт' in name_lower:
                category = 'standard'
            elif 'урвалж' in name_lower:
                category = 'reagent'
            elif any(x in name_lower for x in ['трилон', 'нитрат', 'хлорид', 'сульфат', 'гидроксид']):
                category = 'titrant'

            recipe = SolutionRecipe(
                name=name,
                concentration=conc_val,
                concentration_unit=conc_unit or 'N',
                standard_volume_ml=1000,  # Default
                preparation_notes=prep_notes,
                lab_type='water',
                category=category,
                is_active=True,
            )

            db.session.add(recipe)
            added += 1
            print(f"  + {name} ({conc_str})")

        db.session.commit()
        print(f"\nДүн: {added} жор нэмэгдлээ, {skipped} алгасав.")


if __name__ == '__main__':
    seed_recipes()
