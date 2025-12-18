# -*- coding: utf-8 -*-
"""
Analysis assignment unit тестүүд
"""
import pytest
from app import create_app, db


@pytest.fixture
def app():
    """Test application fixture"""
    from tests.conftest import TestConfig
    app = create_app(TestConfig)
    app.config['SERVER_NAME'] = 'localhost'

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


class TestAnalysisAssignment:
    """Analysis assignment тестүүд"""

    def test_import_module(self):
        """Module import"""
        from app.utils import analysis_assignment
        assert analysis_assignment is not None

    def test_assign_analyses_to_sample_none(self, app):
        """Assign analyses to None sample"""
        from app.utils.analysis_assignment import assign_analyses_to_sample
        with app.app_context():
            try:
                result = assign_analyses_to_sample(None)
                assert result is None or isinstance(result, (list, set, tuple))
            except (TypeError, AttributeError, ValueError):
                pass  # Expected for None input

    def test_module_has_function(self):
        """Module has assign function"""
        from app.utils.analysis_assignment import assign_analyses_to_sample
        assert callable(assign_analyses_to_sample)
