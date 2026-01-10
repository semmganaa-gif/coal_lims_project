# -*- coding: utf-8 -*-
"""
Washability Excel Import Module

Washability Report Excel файлыг уншиж, database-д хадгалах.
Excel бүтэц:
- Front: Тайлангийн мэдээлэл
- Raw Coal analysis: Анхны нүүрсний шинжилгээ
- Float sink: Float-sink дата
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import re
import os

from app import db
from app.models import WashabilityTest, WashabilityFraction, TheoreticalYield
from app.utils.washability import (
    FractionData, calculate_theoretical_yield
)


def parse_date(value) -> Optional[datetime]:
    """Огноо parse хийх"""
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        # Try different formats
        for fmt in ['%Y.%m.%d', '%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def parse_float(value) -> Optional[float]:
    """Float утга parse хийх"""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Remove any non-numeric characters except . and -
        cleaned = re.sub(r'[^\d.\-]', '', value)
        if cleaned:
            try:
                return float(cleaned)
            except ValueError:
                return None
    return None


def read_front_sheet(excel_file: pd.ExcelFile) -> Dict:
    """
    Front sheet-ээс тайлангийн мэдээлэл уншиx.

    Returns:
        {
            'lab_number': '#25_45',
            'sample_name': 'PR12_B23_ST129_4A',
            'report_date': date,
            'sample_date': date,
            'consignor': 'Process engineers team'
        }
    """
    df = pd.read_excel(excel_file, sheet_name='Front', header=None)

    data = {}

    # Search for specific labels and get adjacent values
    for idx, row in df.iterrows():
        for col_idx, cell in enumerate(row):
            if pd.notna(cell) and isinstance(cell, str):
                cell_lower = cell.lower().strip()

                if 'laboratory number' in cell_lower:
                    # Lab number is usually in the last column of same row
                    for c in range(len(row) - 1, col_idx, -1):
                        if pd.notna(row.iloc[c]):
                            data['lab_number'] = str(row.iloc[c])
                            break

                elif 'sample name' in cell_lower:
                    for c in range(len(row) - 1, col_idx, -1):
                        if pd.notna(row.iloc[c]):
                            data['sample_name'] = str(row.iloc[c])
                            break

                elif 'date of report' in cell_lower:
                    for c in range(len(row) - 1, col_idx, -1):
                        if pd.notna(row.iloc[c]):
                            data['report_date'] = parse_date(row.iloc[c])
                            break

                elif 'date of sample received' in cell_lower or 'sampled date' in cell_lower:
                    for c in range(len(row) - 1, col_idx, -1):
                        if pd.notna(row.iloc[c]):
                            data['sample_date'] = parse_date(row.iloc[c])
                            break

                elif 'consignor' in cell_lower:
                    for c in range(len(row) - 1, col_idx, -1):
                        if pd.notna(row.iloc[c]):
                            data['consignor'] = str(row.iloc[c])
                            break

    return data


def read_raw_coal_analysis(excel_file: pd.ExcelFile) -> Dict:
    """
    Raw Coal analysis sheet-ээс анхны нүүрсний шинжилгээ уншиx.

    Returns:
        {
            'initial_mass_kg': 15,
            'raw_tm': 2.63,
            'raw_im': 0.51,
            'raw_ash': 18.05,
            ...
        }
    """
    df = pd.read_excel(excel_file, sheet_name='Raw Coal analysis', header=None)

    data = {}

    # Mapping of Excel labels to our field names
    field_map = {
        'initial mass': 'initial_mass_kg',
        'tm': 'raw_tm',
        'im': 'raw_im',
        'ash': 'raw_ash',
        'vol': 'raw_vol',
        'csn': 'raw_csn',
        'g index': 'raw_gi',
        'sulphur': 'raw_sulphur',
        'trd': 'raw_trd',
    }

    for idx, row in df.iterrows():
        for col_idx, cell in enumerate(row):
            if pd.notna(cell) and isinstance(cell, str):
                cell_lower = cell.lower().strip()

                for label, field in field_map.items():
                    if label in cell_lower:
                        # Get value from next column(s)
                        for c in range(col_idx + 1, len(row)):
                            val = row.iloc[c]
                            if pd.notna(val) and not isinstance(val, str):
                                data[field] = parse_float(val)
                                break
                            elif pd.notna(val) and isinstance(val, str):
                                parsed = parse_float(val)
                                if parsed is not None:
                                    data[field] = parsed
                                    break
                        break

    return data


def read_float_sink_sheet(excel_file: pd.ExcelFile) -> Dict[str, List[Dict]]:
    """
    Float sink sheet-ээс бүх size fraction-ийн дата уншиx.

    Returns:
        {
            '-50+16': [
                {'density_sink': 1.25, 'density_float': 1.3, 'mass_gram': 647.5, ...},
                ...
            ],
            '-16+8': [...],
            ...
        }
    """
    df = pd.read_excel(excel_file, sheet_name='Float sink', header=None)

    size_fractions = {}
    current_size = None
    current_size_mass = None

    # Column indices (may vary, but typical structure)
    # Find header row to determine column positions
    col_map = {}

    for idx, row in df.iterrows():
        row_values = [str(v).lower() if pd.notna(v) else '' for v in row]
        row_str = ' '.join(row_values)

        # Check if this is a header row
        if 'density fraction' in row_str or 'sink' in row_str and 'float' in row_str:
            for c, val in enumerate(row):
                if pd.notna(val):
                    val_lower = str(val).lower()
                    if 'sink' in val_lower:
                        col_map['sink'] = c
                    elif 'float' in val_lower:
                        col_map['float'] = c
                    elif 'gram' in val_lower or 'mass' in val_lower:
                        if 'gram' not in col_map:
                            col_map['gram'] = c
                    elif val_lower == '(%)' or 'mass' in val_lower:
                        if 'percent' not in col_map and c != col_map.get('gram'):
                            col_map['percent'] = c
                    elif 'im' in val_lower:
                        col_map['im'] = c
                    elif 'ash' in val_lower:
                        col_map['ash'] = c
                    elif 'vol' in val_lower:
                        col_map['vol'] = c
                    elif 'sulphur' in val_lower:
                        col_map['sulphur'] = c
                    elif 'csn' in val_lower:
                        col_map['csn'] = c
            continue

        # Check if this is a size fraction header row (e.g., "-50  16.00")
        for c, val in enumerate(row):
            if pd.notna(val):
                val_str = str(val)
                # Check for size fraction pattern
                if val_str.startswith('-') and any(char.isdigit() for char in val_str):
                    # This might be a size fraction
                    # Look for the lower bound in next columns
                    upper = parse_float(val_str.replace('-', ''))
                    for c2 in range(c + 1, min(c + 3, len(row))):
                        if pd.notna(row.iloc[c2]):
                            lower = parse_float(row.iloc[c2])
                            if lower is not None and upper is not None:
                                current_size = f"-{upper}+{lower}"
                                # Look for total mass
                                for c3 in range(c2 + 1, len(row)):
                                    if pd.notna(row.iloc[c3]):
                                        current_size_mass = parse_float(row.iloc[c3])
                                        break
                                size_fractions[current_size] = []
                                break

        # Check if this is a data row (has density values)
        if current_size and col_map.get('sink') is not None:
            sink_val = row.iloc[col_map['sink']] if col_map['sink'] < len(row) else None
            float_val = row.iloc[col_map['float']] if col_map.get('float', 999) < len(row) else None

            if pd.notna(sink_val) and pd.notna(float_val):
                sink = parse_float(sink_val)
                flt = parse_float(float_val)

                if sink is not None and flt is not None:
                    # This is a data row
                    fraction_data = {
                        'density_sink': sink,
                        'density_float': flt,
                        'size_mass': current_size_mass
                    }

                    # Get other values
                    if col_map.get('gram') and col_map['gram'] < len(row):
                        fraction_data['mass_gram'] = parse_float(row.iloc[col_map['gram']])

                    if col_map.get('percent') and col_map['percent'] < len(row):
                        fraction_data['mass_percent'] = parse_float(row.iloc[col_map['percent']])

                    if col_map.get('im') and col_map['im'] < len(row):
                        fraction_data['im_percent'] = parse_float(row.iloc[col_map['im']])

                    if col_map.get('ash') and col_map['ash'] < len(row):
                        fraction_data['ash_ad'] = parse_float(row.iloc[col_map['ash']])

                    if col_map.get('vol') and col_map['vol'] < len(row):
                        fraction_data['vol_ad'] = parse_float(row.iloc[col_map['vol']])

                    if col_map.get('sulphur') and col_map['sulphur'] < len(row):
                        fraction_data['sulphur_ad'] = parse_float(row.iloc[col_map['sulphur']])

                    if col_map.get('csn') and col_map['csn'] < len(row):
                        fraction_data['csn'] = parse_float(row.iloc[col_map['csn']])

                    # Only add if we have valid mass and ash
                    if fraction_data.get('mass_gram') and fraction_data.get('ash_ad') is not None:
                        size_fractions[current_size].append(fraction_data)

        # Check for "Total" row - reset for next size fraction
        for c, val in enumerate(row):
            if pd.notna(val) and str(val).lower().strip() == 'total':
                current_size = None
                break

    return size_fractions


def import_washability_excel(file_path: str, user_id: int = None) -> WashabilityTest:
    """
    Excel файлаас washability test импортлох.

    Args:
        file_path: Excel файлын зам
        user_id: Импорт хийж буй хэрэглэгчийн ID

    Returns:
        WashabilityTest объект
    """
    excel_file = pd.ExcelFile(file_path)
    filename = os.path.basename(file_path)

    # 1. Read metadata from Front sheet
    front_data = read_front_sheet(excel_file)

    # 2. Read raw coal analysis
    raw_data = read_raw_coal_analysis(excel_file)

    # 3. Read float-sink data
    size_fractions = read_float_sink_sheet(excel_file)

    # 4. Create WashabilityTest record
    test = WashabilityTest(
        lab_number=front_data.get('lab_number'),
        sample_name=front_data.get('sample_name'),
        sample_date=front_data.get('sample_date'),
        report_date=front_data.get('report_date'),
        consignor=front_data.get('consignor'),
        initial_mass_kg=raw_data.get('initial_mass_kg'),
        raw_tm=raw_data.get('raw_tm'),
        raw_im=raw_data.get('raw_im'),
        raw_ash=raw_data.get('raw_ash'),
        raw_vol=raw_data.get('raw_vol'),
        raw_sulphur=raw_data.get('raw_sulphur'),
        raw_csn=raw_data.get('raw_csn'),
        raw_gi=raw_data.get('raw_gi'),
        raw_trd=raw_data.get('raw_trd'),
        source='excel',
        excel_filename=filename,
        created_by_id=user_id
    )

    db.session.add(test)
    db.session.flush()  # Get test.id

    # 5. Create WashabilityFraction records
    for size_name, fractions in size_fractions.items():
        # Parse size bounds
        size_parts = size_name.replace('-', '').split('+')
        size_upper = parse_float(size_parts[0]) if len(size_parts) > 0 else None
        size_lower = parse_float(size_parts[1]) if len(size_parts) > 1 else None

        # Get size mass from first fraction
        size_mass = fractions[0].get('size_mass') if fractions else None

        for frac_data in fractions:
            fraction = WashabilityFraction(
                test_id=test.id,
                size_fraction=size_name,
                size_upper=size_upper,
                size_lower=size_lower,
                size_mass_kg=size_mass,
                density_sink=frac_data.get('density_sink'),
                density_float=frac_data.get('density_float'),
                mass_gram=frac_data.get('mass_gram'),
                mass_percent=frac_data.get('mass_percent'),
                im_percent=frac_data.get('im_percent'),
                ash_ad=frac_data.get('ash_ad'),
                vol_ad=frac_data.get('vol_ad'),
                sulphur_ad=frac_data.get('sulphur_ad'),
                csn=frac_data.get('csn')
            )
            db.session.add(fraction)

    db.session.commit()

    # 6. Calculate cumulative values for each fraction
    calculate_and_store_cumulative(test)

    return test


def calculate_and_store_cumulative(test: WashabilityTest):
    """
    Test-ийн бүх fraction-д cumulative values тооцоолж хадгалах.
    """
    # Group fractions by size
    size_groups = {}
    for fraction in test.fractions.all():
        if fraction.size_fraction not in size_groups:
            size_groups[fraction.size_fraction] = []
        size_groups[fraction.size_fraction].append(fraction)

    # Calculate cumulative for each size group
    for size_name, fractions in size_groups.items():
        # Sort by density
        fractions.sort(key=lambda x: x.density_float or 0)

        cum_yield = 0.0
        cum_yield_ash = 0.0

        for frac in fractions:
            if frac.mass_percent and frac.ash_ad is not None:
                cum_yield += frac.mass_percent
                cum_yield_ash += frac.mass_percent * frac.ash_ad

                frac.cumulative_yield = round(cum_yield * 100, 2)
                frac.cumulative_ash = round(cum_yield_ash / cum_yield, 2) if cum_yield > 0 else 0

    db.session.commit()


def calculate_and_store_yields(test: WashabilityTest,
                               target_ashes: List[float] = None):
    """
    Theoretical yield тооцоолж TheoreticalYield хүснэгтэд хадгалах.

    Args:
        test: WashabilityTest объект
        target_ashes: Зорилтот үнслэгүүдийн жагсаалт (default: 8-12% by 0.5)
    """
    if target_ashes is None:
        target_ashes = [8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0]

    # Delete existing yields
    TheoreticalYield.query.filter_by(test_id=test.id).delete()

    # Group fractions by size
    size_groups = {}
    for fraction in test.fractions.all():
        if fraction.size_fraction not in size_groups:
            size_groups[fraction.size_fraction] = []

        size_groups[fraction.size_fraction].append(FractionData(
            density_sink=fraction.density_sink or 0,
            density_float=fraction.density_float or 0,
            mass_gram=fraction.mass_gram or 0,
            mass_percent=fraction.mass_percent or 0,
            ash_ad=fraction.ash_ad or 0,
            im_percent=fraction.im_percent,
            vol_ad=fraction.vol_ad,
            sulphur_ad=fraction.sulphur_ad,
            csn=fraction.csn
        ))

    # Calculate yields for each size fraction
    for size_name, fractions in size_groups.items():
        for target_ash in target_ashes:
            result = calculate_theoretical_yield(fractions, target_ash)

            yield_record = TheoreticalYield(
                test_id=test.id,
                target_ash=target_ash,
                size_fraction=size_name,
                theoretical_yield=result.theoretical_yield,
                separation_density=result.separation_density,
                ngm_plus_01=result.ngm_01,
                ngm_plus_02=result.ngm_02
            )
            db.session.add(yield_record)

    # Calculate composite (weighted average by size fraction mass)
    # Get size weights from database
    size_weights = {}
    for fraction in test.fractions.all():
        if fraction.size_fraction and fraction.size_mass_kg:
            size_weights[fraction.size_fraction] = fraction.size_mass_kg

    # If no weights available, use equal weights
    if not size_weights:
        size_weights = {name: 1.0 for name in size_groups.keys()}

    total_weight = sum(size_weights.values())

    for target_ash in target_ashes:
        # Calculate weighted average yield
        weighted_yield = 0.0
        weighted_density = 0.0
        weighted_ngm_01 = 0.0
        weighted_ngm_02 = 0.0

        for size_name, fractions in size_groups.items():
            result = calculate_theoretical_yield(fractions, target_ash)
            weight = size_weights.get(size_name, 0)

            if total_weight > 0 and result.theoretical_yield:
                weight_ratio = weight / total_weight
                weighted_yield += result.theoretical_yield * weight_ratio
                weighted_density += (result.separation_density or 0) * weight_ratio
                weighted_ngm_01 += (result.ngm_01 or 0) * weight_ratio
                weighted_ngm_02 += (result.ngm_02 or 0) * weight_ratio

        yield_record = TheoreticalYield(
            test_id=test.id,
            target_ash=target_ash,
            size_fraction='ALL',
            theoretical_yield=round(weighted_yield, 2),
            separation_density=round(weighted_density, 3),
            ngm_plus_01=round(weighted_ngm_01, 2),
            ngm_plus_02=round(weighted_ngm_02, 2)
        )
        db.session.add(yield_record)

    db.session.commit()


def bulk_import_from_folder(folder_path: str, user_id: int = None) -> List[Dict]:
    """
    Folder дотор байгаа бүх Excel файлуудыг импортлох.

    Args:
        folder_path: Folder зам
        user_id: Хэрэглэгчийн ID

    Returns:
        [{filename, status, message, test_id}, ...]
    """
    results = []

    for filename in os.listdir(folder_path):
        if filename.endswith(('.xlsx', '.xls')):
            file_path = os.path.join(folder_path, filename)

            try:
                test = import_washability_excel(file_path, user_id)
                calculate_and_store_yields(test)

                results.append({
                    'filename': filename,
                    'status': 'success',
                    'message': 'Imported successfully',
                    'test_id': test.id,
                    'lab_number': test.lab_number,
                    'sample_name': test.sample_name
                })

            except Exception as e:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'message': str(e),
                    'test_id': None
                })

    return results
