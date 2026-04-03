# app/labs/__init__.py
"""
Multi-lab registry.

INSTALLED_LABS dict нь бүх бүртгэлтэй лабораториудыг хадгална.
"""

from __future__ import annotations

from app.labs.base import BaseLab
from app.constants.app_config import LAB_TYPES  # noqa: F401 — re-exported for templates

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
