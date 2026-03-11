# app/forms/__init__.py
"""
WTForms package — split by feature domain.

All forms are re-exported here for backward compatibility:
    from app.forms import LoginForm, AddSampleForm, ...
"""

from app.forms.common import latin_only, MultiCheckboxField  # noqa: F401
from app.forms.auth import LoginForm, UserManagementForm, UserProfileForm  # noqa: F401
from app.forms.samples import AddSampleForm  # noqa: F401
from app.forms.analysis_config import SimpleProfileForm, PatternProfileForm  # noqa: F401
from app.forms.reports import KPIReportFilterForm  # noqa: F401
