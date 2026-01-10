# app/repositories/__init__.py
# -*- coding: utf-8 -*-
"""
Repository Layer - Database access abstraction.

Repositories модулиуд нь database query-уудыг нэг дор төвлөрүүлнэ.
Энэ нь:
- Код дахин ашиглах боломж
- Query-уудыг тест хийхэд хялбар
- Database логикийг route/service-аас салгах

Available repositories:
- SampleRepository: Дээжний database operations
- AnalysisResultRepository: Шинжилгээний үр дүнгийн operations
"""

from app.repositories.sample_repository import SampleRepository
from app.repositories.analysis_result_repository import AnalysisResultRepository

__all__ = [
    "SampleRepository",
    "AnalysisResultRepository",
]
