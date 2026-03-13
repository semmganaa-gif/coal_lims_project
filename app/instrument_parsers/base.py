# app/instrument_parsers/base.py
# -*- coding: utf-8 -*-
"""
Base parser interface for instrument output files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ParsedReading:
    """Нэг хэмжилтийн parse хийсэн үр дүн."""
    sample_code: str
    analysis_code: str
    value: float
    unit: str = "%"
    raw_data: dict = field(default_factory=dict)
    instrument_name: str = ""
    instrument_type: str = ""


class BaseParser:
    """
    Abstract base class for instrument file parsers.

    Шинэ багаж нэмэхэд энэ class-ыг удамшуулж, parse() method-г хэрэгжүүлнэ.
    """

    instrument_type: str = "unknown"
    supported_extensions: tuple[str, ...] = (".csv", ".txt")

    def can_parse(self, file_path: str) -> bool:
        """Энэ parser энэ файлыг уншиж чадах эсэх."""
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_extensions

    def parse(self, file_path: str) -> list[ParsedReading]:
        """
        Файлыг parse хийж, хэмжилтийн жагсаалт буцаах.

        Args:
            file_path: Файлын бүтэн зам

        Returns:
            ParsedReading жагсаалт

        Raises:
            ValueError: Файлын формат буруу
            FileNotFoundError: Файл олдсонгүй
        """
        raise NotImplementedError("Subclass must implement parse()")

    def _read_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """Файл уншиж text буцаах (encoding detect)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Try utf-8 first, then fallback encodings
        for enc in (encoding, "utf-8-sig", "cp1252", "latin-1"):
            try:
                return path.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue

        raise ValueError(f"Cannot decode file: {file_path}")
