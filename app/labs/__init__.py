# app/labs/__init__.py
"""
Multi-lab registry.

INSTALLED_LABS dict нь бүх бүртгэлтэй лабораториудыг хадгална.
"""

from app.labs.base import BaseLab

INSTALLED_LABS = {}


def register_lab(lab_instance: BaseLab):
    """Лаборатори бүртгэх."""
    INSTALLED_LABS[lab_instance.key] = lab_instance


def get_lab(key: str) -> BaseLab | None:
    """Лаборатори авах."""
    return INSTALLED_LABS.get(key)


def get_all_labs() -> dict:
    """Бүх лабораториудыг авах."""
    return INSTALLED_LABS


# Lab types тогтмол
LAB_TYPES = {
    'coal': {'name': 'Нүүрсний лаборатори', 'icon': 'bi-fire', 'color': '#dc3545'},
    'petrography': {'name': 'Петрограф лаборатори', 'icon': 'bi-gem', 'color': '#6f42c1'},
    'water_lab': {'name': 'Усны лаборатори', 'icon': 'bi-droplet-fill', 'color': '#0891b2'},
    'water': {'name': 'Хими лаборатори', 'icon': 'bi-droplet-half', 'color': '#0dcaf0', 'parent': 'water_lab'},
    'microbiology': {'name': 'Микробиологийн лаборатори', 'icon': 'bi-bug', 'color': '#20c997', 'parent': 'water_lab'},
}
