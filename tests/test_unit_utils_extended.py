# -*- coding: utf-8 -*-
"""
Utils extended тестүүд
"""
import pytest
from app import create_app


@pytest.fixture
def app():
    """Test application fixture"""
    app = create_app()
    app.config['TESTING'] = True
    return app


class TestSecurityUtils:
    """Security utils тестүүд"""

    def test_import_security(self):
        """Security module import"""
        from app.utils import security
        assert security is not None

    def test_security_module_has_content(self):
        """Security module has content"""
        from app.utils import security
        assert hasattr(security, '__name__')


class TestSettingsUtils:
    """Settings utils тестүүд"""

    def test_import_settings(self):
        """Settings module import"""
        from app.utils import settings
        assert settings is not None

    @pytest.mark.skip(reason="Requires PostgreSQL database")
    def test_get_sample_type_choices_map(self, app):
        """Get sample type choices map"""
        from app.utils.settings import get_sample_type_choices_map
        with app.app_context():
            result = get_sample_type_choices_map()
            assert isinstance(result, dict)

    @pytest.mark.skip(reason="Requires PostgreSQL database")
    def test_get_unit_abbreviations(self, app):
        """Get unit abbreviations"""
        from app.utils.settings import get_unit_abbreviations
        with app.app_context():
            result = get_unit_abbreviations()
            assert isinstance(result, dict)


class TestAnalysisRulesUtils:
    """Analysis rules utils тестүүд"""

    def test_import_analysis_rules(self):
        """Analysis rules module import"""
        from app.utils import analysis_rules
        assert analysis_rules is not None

    def test_soft_limits_exist(self):
        """Soft limits exist"""
        from app.utils.analysis_rules import SOFT_LIMITS
        assert SOFT_LIMITS is not None


class TestParametersUtils:
    """Parameters utils тестүүд"""

    def test_import_parameters(self):
        """Parameters module import"""
        from app.utils import parameters
        assert parameters is not None


class TestRepeatabilityLoader:
    """Repeatability loader тестүүд"""

    def test_import_repeatability_loader(self):
        """Repeatability loader import"""
        from app.utils import repeatability_loader
        assert repeatability_loader is not None

    def test_module_has_function(self):
        """Module has clear_cache function"""
        from app.utils import repeatability_loader
        assert hasattr(repeatability_loader, 'clear_cache')


class TestAuditUtils:
    """Audit utils тестүүд"""

    def test_import_audit(self):
        """Audit module import"""
        from app.utils import audit
        assert audit is not None


class TestDatetimeUtils:
    """Datetime utils тестүүд"""

    def test_import_datetime(self):
        """Datetime module import"""
        from app.utils import datetime
        assert datetime is not None

    def test_now_local(self, app):
        """now_local function"""
        from app.utils.datetime import now_local
        with app.app_context():
            result = now_local()
            from datetime import datetime as dt
            assert isinstance(result, dt)
