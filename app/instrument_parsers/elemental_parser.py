# app/instrument_parsers/elemental_parser.py
# -*- coding: utf-8 -*-
"""
Elemental Analyzer (CHNS) output parser.

Measures: Total Sulfur (St,d), Carbon, Hydrogen, Nitrogen.
Common instruments: LECO CHN-628, Elementar vario MACRO, 5E-CHN2200.

Expected CSV format:
  Sample ID,Carbon %,Hydrogen %,Nitrogen %,Sulfur %
  CHPP-2026-001,72.50,4.20,1.30,0.85
"""

import csv
import io

from app.instrument_parsers.base import BaseParser, ParsedReading

_COLUMN_MAP = {
    "sulfur": "St,d",
    "sulfur %": "St,d",
    "total sulfur": "St,d",
    "s %": "St,d",
    "st": "St,d",
    "st,d": "St,d",
    "carbon": "Cd",
    "carbon %": "Cd",
    "total carbon": "Cd",
    "c %": "Cd",
    "hydrogen": "Hd",
    "hydrogen %": "Hd",
    "h %": "Hd",
    "nitrogen": "Nd",
    "nitrogen %": "Nd",
    "n %": "Nd",
    "oxygen": "Od",
    "oxygen %": "Od",
    "o %": "Od",
}

_SAMPLE_COLUMNS = {"sample id", "sample_id", "sample", "sample code", "sample_code", "id", "name"}


class ElementalParser(BaseParser):
    instrument_type = "elemental"
    supported_extensions = (".csv", ".txt")

    def parse(self, file_path: str) -> list[ParsedReading]:
        text = self._read_file(file_path)
        reader = csv.DictReader(io.StringIO(text))

        if not reader.fieldnames:
            raise ValueError("Empty or invalid Elemental Analyzer file")

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
                f"No elemental analysis columns found. Expected: carbon, hydrogen, nitrogen, sulfur, etc. "
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
                    instrument_name="Elemental Analyzer",
                    instrument_type=self.instrument_type,
                ))

        return readings
