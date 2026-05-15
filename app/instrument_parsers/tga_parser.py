# app/instrument_parsers/tga_parser.py
# -*- coding: utf-8 -*-
"""
TGA (Thermogravimetric Analyzer) output parser.

Proximate analysis: Moisture (Mad), Ash (Aad), Volatile Matter (Vdaf).
Common instruments: LECO TGA-701, 5E-MAG6700, Eltra TGA.

Expected CSV format (common TGA export):
  Sample ID,Moisture %,Ash %,Volatile %,Fixed Carbon %
  CHPP-2026-001,8.42,12.50,28.30,50.78
"""

import csv
import io

from app.instrument_parsers.base import BaseParser, ParsedReading

# Column name → analysis_code mapping (case-insensitive)
_COLUMN_MAP = {
    "moisture": "Mad",
    "moisture %": "Mad",
    "m %": "Mad",
    "im": "Mad",
    "inherent moisture": "Mad",
    "ash": "Aad",
    "ash %": "Aad",
    "a %": "Aad",
    "volatile": "Vdaf",
    "volatile %": "Vdaf",
    "volatile matter": "Vdaf",
    "vm": "Vdaf",
    "vm %": "Vdaf",
    "fixed carbon": "FCd",
    "fixed carbon %": "FCd",
    "fc": "FCd",
    "fc %": "FCd",
}

# Sample ID column name variants
_SAMPLE_COLUMNS = {"sample id", "sample_id", "sample", "sample code", "sample_code", "id", "name"}


class TGAParser(BaseParser):
    instrument_type = "tga"
    supported_extensions = (".csv", ".txt")

    def parse(self, file_path: str) -> list[ParsedReading]:
        text = self._read_file(file_path)
        reader = csv.DictReader(io.StringIO(text))

        if not reader.fieldnames:
            raise ValueError("Empty or invalid TGA file")

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
                f"No analysis columns found. Expected: moisture, ash, volatile, etc. "
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
                # Remove % sign if present
                value_str = value_str.rstrip("%").strip()
                try:
                    value = float(value_str)
                except ValueError:
                    continue

                readings.append(ParsedReading(
                    sample_code=sample_code,
                    analysis_code=analysis_code,
                    value=value,
                    unit="%",
                    raw_data={k: v for k, v in row.items()},
                    instrument_name="TGA",
                    instrument_type=self.instrument_type,
                ))

        return readings
