# app/instrument_parsers/bomb_cal_parser.py
# -*- coding: utf-8 -*-
"""
Bomb Calorimeter output parser.

Calorific value: Qgr,ad (gross calorific value, as-determined).
Common instruments: LECO AC-600, IKA C200, Parr 6400, 5E-C5500.

Expected CSV format:
  Sample ID,Gross Cal (MJ/kg),Net Cal (MJ/kg)
  CHPP-2026-001,25.42,24.10
"""

import csv
import io

from app.instrument_parsers.base import BaseParser, ParsedReading

_COLUMN_MAP = {
    "gross cal": "Qgr,ad",
    "gross calorific": "Qgr,ad",
    "gross calorific value": "Qgr,ad",
    "gcv": "Qgr,ad",
    "gross cal (mj/kg)": "Qgr,ad",
    "gross cal (kcal/kg)": "Qgr,ad",
    "qgr": "Qgr,ad",
    "qgr,ad": "Qgr,ad",
    "net cal": "Qnet,ar",
    "net calorific": "Qnet,ar",
    "net calorific value": "Qnet,ar",
    "ncv": "Qnet,ar",
    "net cal (mj/kg)": "Qnet,ar",
    "net cal (kcal/kg)": "Qnet,ar",
    "qnet": "Qnet,ar",
    "qnet,ar": "Qnet,ar",
}

_SAMPLE_COLUMNS = {"sample id", "sample_id", "sample", "sample code", "sample_code", "id", "name"}


class BombCalParser(BaseParser):
    instrument_type = "bomb_cal"
    supported_extensions = (".csv", ".txt")

    def parse(self, file_path: str) -> list[ParsedReading]:
        text = self._read_file(file_path)
        reader = csv.DictReader(io.StringIO(text))

        if not reader.fieldnames:
            raise ValueError("Empty or invalid Bomb Calorimeter file")

        # Find sample column
        fields_lower = {f.strip().lower(): f for f in reader.fieldnames}
        sample_col = None
        for candidate in _SAMPLE_COLUMNS:
            if candidate in fields_lower:
                sample_col = fields_lower[candidate]
                break

        if sample_col is None:
            raise ValueError(
                f"No sample ID column found. Expected one of: {_SAMPLE_COLUMNS}. "
                f"Found: {list(reader.fieldnames)}"
            )

        # Map columns to analysis codes
        col_to_code = {}
        for col in reader.fieldnames:
            col_lower = col.strip().lower()
            if col_lower in _COLUMN_MAP:
                col_to_code[col] = _COLUMN_MAP[col_lower]

        if not col_to_code:
            raise ValueError(
                f"No calorific value columns found. Expected: gross cal, gcv, net cal, etc. "
                f"Found: {list(reader.fieldnames)}"
            )

        readings = []
        for row in reader:
            sample_code = (row.get(sample_col) or "").strip()
            if not sample_code:
                continue

            for col, analysis_code in col_to_code.items():
                value_str = (row.get(col) or "").strip()
                if not value_str:
                    continue
                try:
                    value = float(value_str)
                except ValueError:
                    continue

                readings.append(ParsedReading(
                    sample_code=sample_code,
                    analysis_code=analysis_code,
                    value=value,
                    unit="MJ/kg",
                    raw_data={k: v for k, v in row.items()},
                    instrument_name="Bomb Calorimeter",
                    instrument_type=self.instrument_type,
                ))

        return readings
