# app/instrument_parsers/generic_csv.py
# -*- coding: utf-8 -*-
"""
Generic CSV parser — хамгийн энгийн формат.

Expected CSV format:
  sample_code,analysis_code,value[,unit]
  CHPP-2026-001,Mad,8.42,%
  CHPP-2026-001,Aad,12.5,%
"""

import csv
import io

from app.instrument_parsers.base import BaseParser, ParsedReading


class GenericCSVParser(BaseParser):
    instrument_type = "generic_csv"
    supported_extensions = (".csv",)

    def parse(self, file_path: str) -> list[ParsedReading]:
        text = self._read_file(file_path)
        reader = csv.DictReader(io.StringIO(text))

        # Validate headers
        required = {"sample_code", "analysis_code", "value"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"CSV must have columns: {required}. "
                f"Found: {reader.fieldnames}"
            )

        readings = []
        for i, row in enumerate(reader):
            sample_code = (row.get("sample_code") or "").strip()
            analysis_code = (row.get("analysis_code") or "").strip()
            value_str = (row.get("value") or "").strip()

            if not sample_code or not analysis_code or not value_str:
                continue

            try:
                value = float(value_str)
            except ValueError:
                continue

            readings.append(ParsedReading(
                sample_code=sample_code,
                analysis_code=analysis_code,
                value=value,
                unit=(row.get("unit") or "%").strip(),
                raw_data=dict(row),
                instrument_name="Generic CSV",
                instrument_type=self.instrument_type,
            ))

        return readings
