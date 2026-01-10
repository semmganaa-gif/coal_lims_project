"""
Шинжилгээний кодын нормчлол ба alias удирдлага.

Alias кодуудыг base код руу хөрвүүлэх, жагсаалт болгох зэрэг.
"""
from typing import Iterable, List, Set, Dict
from app.constants import ALIAS_TO_BASE_ANALYSIS


def _lc(s: str) -> str:
    """String-г lowercase болгох."""
    return "" if s is None else str(s).strip().lower()


def norm_code(code: str) -> str:
    """Alias (St,ad / Mt,ar ...) -> base (TS / MT ...) болгож нэг мөр нормчилно."""
    if not code:
        return code
    return ALIAS_TO_BASE_ANALYSIS.get(_lc(code), code)


def to_base_list(codes: Iterable[str] | None) -> List[str]:
    """Кодуудын жагсаалтыг base код руу хөрвүүлэх."""
    if not codes:
        return []
    return [norm_code(c) for c in codes]


# Base -> aliases (lowercase) зураглал
BASE_TO_ALIASES: Dict[str, Set[str]] = {}
for alias_lc, base in ALIAS_TO_BASE_ANALYSIS.items():
    if not base:
        continue
    BASE_TO_ALIASES.setdefault(base, set()).add(alias_lc)   # алиасууд (аль хэдийн lowercase)
    BASE_TO_ALIASES[base].add(base.lower())                 # base өөрийг нь бас alias гэж үзнэ


def aliases_of(base_code: str) -> Set[str]:
    """Тухайн base кодын бүх алиасыг (lowercase) буцаана."""
    return BASE_TO_ALIASES.get(base_code, set())


def is_alias_of_base(code: str, base_code: str) -> bool:
    """Өгөгдсөн code нь тухайн base-ийн алиас мөн эсэх."""
    if not code:
        return False
    return _lc(code) in BASE_TO_ALIASES.get(base_code, set())
