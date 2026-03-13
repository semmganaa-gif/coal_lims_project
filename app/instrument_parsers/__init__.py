# app/instrument_parsers/__init__.py
# -*- coding: utf-8 -*-
"""
Instrument output file parsers.

Багаж бүрийн гаралтын файлыг parse хийх модулиуд.
Шинэ багаж нэмэхэд зөвхөн шинэ parser class нэмэхэд хангалттай.

Supported instruments:
  - GenericCSV: Ерөнхий CSV формат (sample_code, analysis_code, value)
  - TGA: Thermogravimetric Analyzer (moisture, ash, volatile)
  - BombCalorimeter: Calorific value (Qgr,ad)
  - ElementalAnalyzer: CHNS (St,d, carbon, hydrogen, nitrogen)
"""

from app.instrument_parsers.base import BaseParser, ParsedReading
from app.instrument_parsers.generic_csv import GenericCSVParser
from app.instrument_parsers.tga_parser import TGAParser
from app.instrument_parsers.bomb_cal_parser import BombCalParser
from app.instrument_parsers.elemental_parser import ElementalParser

# Parser registry — instrument_type → parser class
PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    "generic_csv": GenericCSVParser,
    "tga": TGAParser,
    "bomb_cal": BombCalParser,
    "elemental": ElementalParser,
}


def get_parser(instrument_type: str) -> BaseParser:
    """Instrument type-аар parser авах."""
    parser_cls = PARSER_REGISTRY.get(instrument_type)
    if parser_cls is None:
        raise ValueError(f"Unknown instrument type: {instrument_type}. "
                         f"Available: {list(PARSER_REGISTRY.keys())}")
    return parser_cls()


__all__ = [
    "BaseParser",
    "ParsedReading",
    "PARSER_REGISTRY",
    "get_parser",
    "GenericCSVParser",
    "TGAParser",
    "BombCalParser",
    "ElementalParser",
]
