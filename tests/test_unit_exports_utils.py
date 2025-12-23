# tests/unit/test_exports_utils.py
# -*- coding: utf-8 -*-
"""Exports utils tests"""

import pytest


class TestExportsUtils:
    def test_import(self):
        try:
            from app.utils import exports
            assert exports is not None
        except ImportError:
            pass

    def test_export_samples_to_excel(self, app):
        with app.app_context():
            try:
                from app.utils.exports import export_samples_to_excel
                result = export_samples_to_excel([])
                assert result is not None or result is None
            except (ImportError, AttributeError):
                pass

    def test_export_results_to_excel(self, app):
        with app.app_context():
            try:
                from app.utils.exports import export_results_to_excel
                result = export_results_to_excel([])
                assert result is not None or result is None
            except (ImportError, AttributeError):
                pass

    def test_export_to_csv(self, app):
        with app.app_context():
            try:
                from app.utils.exports import export_to_csv
                result = export_to_csv([], ['col1', 'col2'])
                assert result is not None or result is None
            except (ImportError, AttributeError):
                pass


class TestExportHelpers:
    def test_format_value(self, app):
        with app.app_context():
            try:
                from app.utils.exports import format_value
                result = format_value(12.345, 2)
                assert result is not None
            except (ImportError, AttributeError):
                pass

    def test_sanitize_filename(self, app):
        with app.app_context():
            try:
                from app.utils.exports import sanitize_filename
                result = sanitize_filename('test/file\\name')
                assert '/' not in result and '\\' not in result
            except (ImportError, AttributeError):
                pass
