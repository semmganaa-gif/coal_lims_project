# tests/test_routes_quality_batch.py
"""
Comprehensive tests for quality route modules:
- capa.py
- improvement.py
- nonconformity.py
- environmental.py
- proficiency.py

Target: 80%+ coverage for all five files.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import date

from flask import Flask, Blueprint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_user(user_id=1, username="testuser", role="admin"):
    u = MagicMock()
    u.id = user_id
    u.username = username
    u.role = role
    u.is_authenticated = True
    u.is_active = True
    u.is_anonymous = False
    u.get_id.return_value = str(user_id)
    return u


def _noop_decorator(endpoint=None):
    """Replacement for require_quality_edit that does nothing."""
    def decorator(f):
        return f
    return decorator


def _noop_login_required(f):
    return f


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """Create a minimal Flask app with the quality blueprint."""
    application = Flask(__name__)
    application.config['TESTING'] = True
    application.config['SECRET_KEY'] = 'test-secret'
    application.config['WTF_CSRF_ENABLED'] = False
    application.config['SERVER_NAME'] = 'localhost'

    return application


@pytest.fixture()
def mock_user():
    return _make_mock_user()


# =========================================================================
# CAPA tests
# =========================================================================

class TestCapaRoutes:
    """Tests for app/routes/quality/capa.py"""

    @pytest.fixture(autouse=True)
    def setup(self, app, mock_user):
        self.app = app
        self.mock_user = mock_user

        # Patches
        self.patches = []

        p_login = patch(
            'app.routes.quality.capa.login_required', _noop_login_required
        )
        p_qedit = patch(
            'app.routes.quality.capa.require_quality_edit', _noop_decorator
        )
        p_db = patch('app.routes.quality.capa.db')
        p_model = patch('app.routes.quality.capa.CorrectiveAction')
        p_repo = patch('app.routes.quality.capa.CAPARepository')
        p_safe = patch('app.routes.quality.capa.safe_commit')
        p_stats = patch('app.routes.quality.capa.calculate_status_stats')
        p_seqcode = patch('app.routes.quality.capa.generate_sequential_code')
        p_render = patch('app.routes.quality.capa.render_template')
        p_cu = patch('app.routes.quality.capa.current_user', self.mock_user)

        self.patches = [p_login, p_qedit, p_db, p_model, p_repo, p_safe, p_stats,
                        p_seqcode, p_render, p_cu]
        mocks = [p.start() for p in self.patches]
        (self.m_login, self.m_qedit, self.m_db, self.m_model, self.m_repo,
         self.m_safe, self.m_stats, self.m_seqcode, self.m_render, _) = mocks

        self.m_render.return_value = "rendered"
        self.m_safe.return_value = True
        self.m_stats.return_value = {'open': 0, 'in_progress': 0, 'reviewed': 0, 'closed': 0}
        self.m_seqcode.return_value = "CA-001"
        self.m_repo.get_all.return_value = []

        # Register routes
        bp = Blueprint('quality', __name__, url_prefix='/quality')
        from app.routes.quality.capa import register_routes
        register_routes(bp)
        app.register_blueprint(bp)

        self.client = app.test_client()

        yield

        for p in self.patches:
            p.stop()

    # -- capa_list --

    def test_capa_list_success(self):
        self.m_repo.get_all.return_value = []

        with self.app.app_context():
            resp = self.client.get('/quality/capa')
        assert resp.status_code == 200
        self.m_render.assert_called_once()
        call_args = self.m_render.call_args
        assert call_args[0][0] == 'quality/capa_list.html'

    # -- capa_new GET --

    def test_capa_new_get(self):
        with self.app.app_context():
            resp = self.client.get('/quality/capa/new')
        assert resp.status_code == 200
        self.m_render.assert_called_once()
        assert 'quality/capa_form.html' in self.m_render.call_args[0][0]

    # -- capa_new POST success --

    def test_capa_new_post_success(self):
        self.m_safe.return_value = True
        with self.app.app_context():
            resp = self.client.post('/quality/capa/new', data={
                'issue_description': 'Test issue',
                'issue_date': '2026-01-01',
                'corrective_action': 'Fix it',
                'target_date': '2026-02-01',
                'notes': 'Some notes',
            })
        assert resp.status_code == 302
        self.m_repo.save.assert_called_once()

    # -- capa_new POST empty description --

    def test_capa_new_post_empty_description(self):
        with self.app.app_context():
            resp = self.client.post('/quality/capa/new', data={
                'issue_description': '',
            })
        assert resp.status_code == 200
        self.m_render.assert_called_once()

    # -- capa_new POST safe_commit fails --

    def test_capa_new_post_commit_failure(self):
        self.m_safe.return_value = False
        with self.app.app_context():
            resp = self.client.post('/quality/capa/new', data={
                'issue_description': 'Test issue',
            })
        assert resp.status_code == 302

    # -- capa_new POST no target_date --

    def test_capa_new_post_no_target_date(self):
        self.m_safe.return_value = True
        with self.app.app_context():
            resp = self.client.post('/quality/capa/new', data={
                'issue_description': 'Test issue',
                'target_date': '',
            })
        assert resp.status_code == 302

    # -- capa_detail --

    def test_capa_detail_found(self):
        mock_record = MagicMock()
        mock_record.ca_number = "CA-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record

        with self.app.app_context():
            resp = self.client.get('/quality/capa/1')
        assert resp.status_code == 200

    def test_capa_detail_not_found(self):
        from werkzeug.exceptions import NotFound
        self.m_repo.get_by_id_or_404.side_effect = NotFound()
        with self.app.app_context():
            resp = self.client.get('/quality/capa/999')
        assert resp.status_code == 404

    # -- capa_fill --

    def test_capa_fill_success(self):
        mock_record = MagicMock()
        mock_record.ca_number = "CA-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record
        self.m_safe.return_value = True

        with self.app.app_context():
            resp = self.client.post('/quality/capa/1/fill', data={
                'issue_description': 'Updated issue',
                'corrective_action': 'New action',
                'notes': 'Updated notes',
                'target_date': '2026-03-01',
            })
        assert resp.status_code == 302
        assert mock_record.status == 'in_progress'

    def test_capa_fill_not_found(self):
        from werkzeug.exceptions import NotFound
        self.m_repo.get_by_id_or_404.side_effect = NotFound()
        with self.app.app_context():
            resp = self.client.post('/quality/capa/999/fill', data={})
        assert resp.status_code == 404

    def test_capa_fill_commit_failure(self):
        mock_record = MagicMock()
        mock_record.ca_number = "CA-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record
        self.m_safe.return_value = False

        with self.app.app_context():
            resp = self.client.post('/quality/capa/1/fill', data={
                'issue_description': '',
                'corrective_action': '',
                'notes': '',
                'target_date': '',
            })
        assert resp.status_code == 302

    def test_capa_fill_empty_description_keeps_original(self):
        mock_record = MagicMock()
        mock_record.ca_number = "CA-001"
        mock_record.issue_description = "Original"
        self.m_repo.get_by_id_or_404.return_value = mock_record
        self.m_safe.return_value = True

        with self.app.app_context():
            resp = self.client.post('/quality/capa/1/fill', data={
                'issue_description': '  ',
                'corrective_action': 'action',
                'notes': '',
                'target_date': '',
            })
        # Empty strip => falsy => keeps original via `or record.issue_description`
        assert mock_record.issue_description == "Original"

    # -- capa_review --

    def test_capa_review_success(self):
        mock_record = MagicMock()
        mock_record.ca_number = "CA-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record
        self.m_safe.return_value = True

        with self.app.app_context():
            resp = self.client.post('/quality/capa/1/review', data={
                'completed_on_time': '1',
                'fully_resolved': '1',
                'residual_risk_exists': '0',
                'management_change_needed': '0',
                'control_notes': 'All good',
            })
        assert resp.status_code == 302
        assert mock_record.status == 'reviewed'
        assert mock_record.completed_on_time is True
        assert mock_record.fully_resolved is True
        assert mock_record.residual_risk_exists is False
        assert mock_record.management_change_needed is False
        assert mock_record.technical_manager_id == 1

    def test_capa_review_not_found(self):
        from werkzeug.exceptions import NotFound
        self.m_repo.get_by_id_or_404.side_effect = NotFound()
        with self.app.app_context():
            resp = self.client.post('/quality/capa/999/review', data={})
        assert resp.status_code == 404

    def test_capa_review_commit_failure(self):
        mock_record = MagicMock()
        mock_record.ca_number = "CA-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record
        self.m_safe.return_value = False

        with self.app.app_context():
            resp = self.client.post('/quality/capa/1/review', data={
                'completed_on_time': '1',
                'fully_resolved': '0',
                'residual_risk_exists': '1',
                'management_change_needed': '1',
                'control_notes': '',
            })
        assert resp.status_code == 302


# =========================================================================
# Improvement tests
# =========================================================================

class TestImprovementRoutes:
    """Tests for app/routes/quality/improvement.py"""

    @pytest.fixture(autouse=True)
    def setup(self, app, mock_user):
        self.app = app
        self.mock_user = mock_user

        self.patches = []

        p_login = patch(
            'app.routes.quality.improvement.login_required', _noop_login_required
        )
        p_qedit = patch(
            'app.routes.quality.improvement.require_quality_edit', _noop_decorator
        )
        p_db = patch('app.routes.quality.improvement.db')
        p_model = patch('app.routes.quality.improvement.ImprovementRecord')
        p_repo = patch('app.routes.quality.improvement.ImprovementRepository')
        p_safe = patch('app.routes.quality.improvement.safe_commit')
        p_stats = patch('app.routes.quality.improvement.calculate_status_stats')
        p_seqcode = patch('app.routes.quality.improvement.generate_sequential_code')
        p_render = patch('app.routes.quality.improvement.render_template')
        p_cu = patch('app.routes.quality.improvement.current_user', self.mock_user)

        self.patches = [p_login, p_qedit, p_db, p_model, p_repo, p_safe, p_stats,
                        p_seqcode, p_render, p_cu]
        mocks = [p.start() for p in self.patches]
        (self.m_login, self.m_qedit, self.m_db, self.m_model, self.m_repo,
         self.m_safe, self.m_stats, self.m_seqcode, self.m_render, _) = mocks

        self.m_render.return_value = "rendered"
        self.m_safe.return_value = True
        self.m_stats.return_value = {}
        self.m_seqcode.return_value = "IMP-001"
        self.m_repo.get_all.return_value = []

        bp = Blueprint('quality', __name__, url_prefix='/quality')
        from app.routes.quality.improvement import register_routes
        register_routes(bp)
        app.register_blueprint(bp)

        self.client = app.test_client()

        yield

        for p in self.patches:
            p.stop()

    # -- improvement_list --

    def test_improvement_list(self):
        self.m_repo.get_all.return_value = []

        with self.app.app_context():
            resp = self.client.get('/quality/improvement')
        assert resp.status_code == 200
        self.m_render.assert_called_once()
        assert 'quality/improvement_list.html' in self.m_render.call_args[0][0]

    # -- improvement_new GET --

    def test_improvement_new_get(self):
        with self.app.app_context():
            resp = self.client.get('/quality/improvement/new')
        assert resp.status_code == 200

    # -- improvement_new POST success --

    def test_improvement_new_post_success(self):
        with self.app.app_context():
            resp = self.client.post('/quality/improvement/new', data={
                'activity_description': 'Improve calibration',
                'record_date': '2026-01-01',
                'improvement_plan': 'Plan A',
                'deadline': '2026-06-01',
                'responsible_person': 'John',
                'documentation': 'Doc ref',
            })
        assert resp.status_code == 302
        self.m_repo.save.assert_called_once()

    # -- improvement_new POST empty activity --

    def test_improvement_new_post_empty_activity(self):
        with self.app.app_context():
            resp = self.client.post('/quality/improvement/new', data={
                'activity_description': '',
            })
        assert resp.status_code == 200
        self.m_render.assert_called_once()

    # -- improvement_new POST commit failure --

    def test_improvement_new_post_commit_failure(self):
        self.m_safe.return_value = False
        with self.app.app_context():
            resp = self.client.post('/quality/improvement/new', data={
                'activity_description': 'Test activity',
            })
        assert resp.status_code == 302

    # -- improvement_new POST no deadline --

    def test_improvement_new_post_no_deadline(self):
        with self.app.app_context():
            resp = self.client.post('/quality/improvement/new', data={
                'activity_description': 'Test',
                'deadline': '',
            })
        assert resp.status_code == 302

    # -- improvement_detail --

    def test_improvement_detail_found(self):
        mock_record = MagicMock()
        mock_record.record_no = "IMP-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record

        with self.app.app_context():
            resp = self.client.get('/quality/improvement/1')
        assert resp.status_code == 200

    def test_improvement_detail_not_found(self):
        from werkzeug.exceptions import NotFound
        self.m_repo.get_by_id_or_404.side_effect = NotFound()
        with self.app.app_context():
            resp = self.client.get('/quality/improvement/999')
        assert resp.status_code == 404

    # -- improvement_fill --

    def test_improvement_fill_success(self):
        mock_record = MagicMock()
        mock_record.record_no = "IMP-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record

        with self.app.app_context():
            resp = self.client.post('/quality/improvement/1/fill', data={
                'activity_description': 'Updated activity',
                'improvement_plan': 'Updated plan',
                'responsible_person': 'Jane',
                'documentation': 'Updated doc',
                'deadline': '2026-07-01',
            })
        assert resp.status_code == 302
        assert mock_record.status == 'in_progress'

    def test_improvement_fill_not_found(self):
        from werkzeug.exceptions import NotFound
        self.m_repo.get_by_id_or_404.side_effect = NotFound()
        with self.app.app_context():
            resp = self.client.post('/quality/improvement/999/fill', data={})
        assert resp.status_code == 404

    def test_improvement_fill_commit_failure(self):
        mock_record = MagicMock()
        mock_record.record_no = "IMP-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record
        self.m_safe.return_value = False

        with self.app.app_context():
            resp = self.client.post('/quality/improvement/1/fill', data={
                'activity_description': '',
                'improvement_plan': '',
                'responsible_person': '',
                'documentation': '',
                'deadline': '',
            })
        assert resp.status_code == 302

    def test_improvement_fill_empty_description_keeps_original(self):
        mock_record = MagicMock()
        mock_record.record_no = "IMP-001"
        mock_record.activity_description = "Original"
        self.m_repo.get_by_id_or_404.return_value = mock_record

        with self.app.app_context():
            resp = self.client.post('/quality/improvement/1/fill', data={
                'activity_description': '  ',
                'deadline': '',
            })
        assert mock_record.activity_description == "Original"

    # -- improvement_review --

    def test_improvement_review_success(self):
        mock_record = MagicMock()
        mock_record.record_no = "IMP-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record

        with self.app.app_context():
            resp = self.client.post('/quality/improvement/1/review', data={
                'completed_on_time': '1',
                'fully_implemented': '1',
                'control_notes': 'Good',
            })
        assert resp.status_code == 302
        assert mock_record.status == 'reviewed'
        assert mock_record.completed_on_time is True
        assert mock_record.fully_implemented is True
        assert mock_record.technical_manager_id == 1

    def test_improvement_review_not_found(self):
        from werkzeug.exceptions import NotFound
        self.m_repo.get_by_id_or_404.side_effect = NotFound()
        with self.app.app_context():
            resp = self.client.post('/quality/improvement/999/review', data={})
        assert resp.status_code == 404

    def test_improvement_review_commit_failure(self):
        mock_record = MagicMock()
        mock_record.record_no = "IMP-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record
        self.m_safe.return_value = False

        with self.app.app_context():
            resp = self.client.post('/quality/improvement/1/review', data={
                'completed_on_time': '0',
                'fully_implemented': '0',
                'control_notes': '',
            })
        assert resp.status_code == 302

    def test_improvement_review_boolean_false_values(self):
        mock_record = MagicMock()
        mock_record.record_no = "IMP-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record

        with self.app.app_context():
            resp = self.client.post('/quality/improvement/1/review', data={
                'completed_on_time': '0',
                'fully_implemented': '0',
                'control_notes': 'Issues found',
            })
        assert resp.status_code == 302
        assert mock_record.completed_on_time is False
        assert mock_record.fully_implemented is False


# =========================================================================
# NonConformity tests
# =========================================================================

class TestNonConformityRoutes:
    """Tests for app/routes/quality/nonconformity.py"""

    @pytest.fixture(autouse=True)
    def setup(self, app, mock_user):
        self.app = app
        self.mock_user = mock_user

        self.patches = []

        p_login = patch(
            'app.routes.quality.nonconformity.login_required', _noop_login_required
        )
        p_qedit = patch(
            'app.routes.quality.nonconformity.require_quality_edit', _noop_decorator
        )
        p_db = patch('app.routes.quality.nonconformity.db')
        p_model = patch('app.routes.quality.nonconformity.NonConformityRecord')
        p_repo = patch('app.routes.quality.nonconformity.NonConformityRepository')
        p_safe = patch('app.routes.quality.nonconformity.safe_commit')
        p_stats = patch('app.routes.quality.nonconformity.calculate_status_stats')
        p_seqcode = patch('app.routes.quality.nonconformity.generate_sequential_code')
        p_render = patch('app.routes.quality.nonconformity.render_template')
        p_cu = patch('app.routes.quality.nonconformity.current_user', self.mock_user)

        self.patches = [p_login, p_qedit, p_db, p_model, p_repo, p_safe, p_stats,
                        p_seqcode, p_render, p_cu]
        mocks = [p.start() for p in self.patches]
        (self.m_login, self.m_qedit, self.m_db, self.m_model, self.m_repo,
         self.m_safe, self.m_stats, self.m_seqcode, self.m_render, _) = mocks

        self.m_render.return_value = "rendered"
        self.m_safe.return_value = True
        self.m_stats.return_value = {}
        self.m_seqcode.return_value = "NC-001"
        self.m_repo.get_all.return_value = []

        bp = Blueprint('quality', __name__, url_prefix='/quality')
        from app.routes.quality.nonconformity import register_routes
        register_routes(bp)
        app.register_blueprint(bp)

        self.client = app.test_client()

        yield

        for p in self.patches:
            p.stop()

    # -- nonconformity_list --

    def test_nonconformity_list(self):
        self.m_repo.get_all.return_value = []

        with self.app.app_context():
            resp = self.client.get('/quality/nonconformity')
        assert resp.status_code == 200
        assert 'quality/nonconformity_list.html' in self.m_render.call_args[0][0]

    # -- nonconformity_new GET --

    def test_nonconformity_new_get(self):
        with self.app.app_context():
            resp = self.client.get('/quality/nonconformity/new')
        assert resp.status_code == 200

    # -- nonconformity_new POST success --

    def test_nonconformity_new_post_success(self):
        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/new', data={
                'detector_name': 'Tester',
                'nc_description': 'Something non-conforming',
                'record_date': '2026-01-15',
                'detector_department': 'QC',
                'proposed_action': 'Investigate',
            })
        assert resp.status_code == 302
        self.m_repo.save.assert_called_once()

    # -- nonconformity_new POST missing detector_name --

    def test_nonconformity_new_post_missing_detector(self):
        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/new', data={
                'detector_name': '',
                'nc_description': 'Some issue',
            })
        assert resp.status_code == 200
        self.m_render.assert_called_once()

    # -- nonconformity_new POST missing nc_description --

    def test_nonconformity_new_post_missing_description(self):
        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/new', data={
                'detector_name': 'Tester',
                'nc_description': '',
            })
        assert resp.status_code == 200

    # -- nonconformity_new POST both empty --

    def test_nonconformity_new_post_both_empty(self):
        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/new', data={
                'detector_name': '',
                'nc_description': '',
            })
        assert resp.status_code == 200

    # -- nonconformity_new POST commit failure --

    def test_nonconformity_new_post_commit_failure(self):
        self.m_safe.return_value = False
        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/new', data={
                'detector_name': 'Tester',
                'nc_description': 'Issue found',
            })
        assert resp.status_code == 302

    # -- nonconformity_detail --

    def test_nonconformity_detail_found(self):
        mock_record = MagicMock()
        mock_record.record_no = "NC-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record

        with self.app.app_context():
            resp = self.client.get('/quality/nonconformity/1')
        assert resp.status_code == 200

    def test_nonconformity_detail_not_found(self):
        from werkzeug.exceptions import NotFound
        self.m_repo.get_by_id_or_404.side_effect = NotFound()
        with self.app.app_context():
            resp = self.client.get('/quality/nonconformity/999')
        assert resp.status_code == 404

    # -- nonconformity_investigate --

    def test_nonconformity_investigate_success(self):
        mock_record = MagicMock()
        mock_record.record_no = "NC-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record

        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/1/investigate', data={
                'responsible_unit': 'Lab A',
                'responsible_person': 'Jane',
                'direct_cause': 'Human error',
                'corrective_action': 'Retrain',
                'corrective_deadline': '2026-04-01',
                'root_cause': 'Lack of training',
                'corrective_plan': 'Full retraining',
            })
        assert resp.status_code == 302
        assert mock_record.status == 'investigating'
        assert mock_record.responsible_user_id == 1

    def test_nonconformity_investigate_not_found(self):
        from werkzeug.exceptions import NotFound
        self.m_repo.get_by_id_or_404.side_effect = NotFound()
        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/999/investigate', data={})
        assert resp.status_code == 404

    def test_nonconformity_investigate_commit_failure(self):
        mock_record = MagicMock()
        mock_record.record_no = "NC-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record
        self.m_safe.return_value = False

        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/1/investigate', data={
                'responsible_unit': '',
                'corrective_deadline': '',
            })
        assert resp.status_code == 302

    def test_nonconformity_investigate_no_deadline(self):
        mock_record = MagicMock()
        mock_record.record_no = "NC-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record

        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/1/investigate', data={
                'responsible_unit': 'Lab B',
                'responsible_person': 'Bob',
                'direct_cause': 'Equipment fault',
                'corrective_action': 'Replace',
                'corrective_deadline': '',
                'root_cause': 'Wear',
                'corrective_plan': 'Replacement schedule',
            })
        assert resp.status_code == 302
        assert mock_record.corrective_deadline is None

    # -- nonconformity_review --

    def test_nonconformity_review_success(self):
        mock_record = MagicMock()
        mock_record.record_no = "NC-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record

        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/1/review', data={
                'completed_on_time': '1',
                'fully_implemented': '1',
                'control_notes': 'Verified',
            })
        assert resp.status_code == 302
        assert mock_record.status == 'reviewed'
        assert mock_record.completed_on_time is True
        assert mock_record.fully_implemented is True
        assert mock_record.manager_id == 1

    def test_nonconformity_review_not_found(self):
        from werkzeug.exceptions import NotFound
        self.m_repo.get_by_id_or_404.side_effect = NotFound()
        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/999/review', data={})
        assert resp.status_code == 404

    def test_nonconformity_review_commit_failure(self):
        mock_record = MagicMock()
        mock_record.record_no = "NC-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record
        self.m_safe.return_value = False

        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/1/review', data={
                'completed_on_time': '0',
                'fully_implemented': '0',
                'control_notes': '',
            })
        assert resp.status_code == 302

    def test_nonconformity_review_false_booleans(self):
        mock_record = MagicMock()
        mock_record.record_no = "NC-001"
        self.m_repo.get_by_id_or_404.return_value = mock_record

        with self.app.app_context():
            resp = self.client.post('/quality/nonconformity/1/review', data={
                'completed_on_time': '0',
                'fully_implemented': '0',
                'control_notes': 'Not resolved',
            })
        assert mock_record.completed_on_time is False
        assert mock_record.fully_implemented is False


# =========================================================================
# Environmental tests
# =========================================================================

class TestEnvironmentalRoutes:
    """Tests for app/routes/quality/environmental.py"""

    @pytest.fixture(autouse=True)
    def setup(self, app, mock_user):
        self.app = app
        self.mock_user = mock_user

        self.patches = []

        p_login = patch(
            'app.routes.quality.environmental.login_required', _noop_login_required
        )
        p_qedit = patch(
            'app.routes.quality.environmental.require_quality_edit', _noop_decorator
        )
        p_db = patch('app.routes.quality.environmental.db')
        p_model = patch('app.routes.quality.environmental.EnvironmentalLog')
        p_repo = patch('app.routes.quality.environmental.EnvironmentalLogRepository')
        p_safe = patch('app.routes.quality.environmental.safe_commit')
        p_render = patch('app.routes.quality.environmental.render_template')
        p_flash = patch('app.routes.quality.environmental.flash')
        p_cu = patch('app.routes.quality.environmental.current_user', self.mock_user)

        self.patches = [p_login, p_qedit, p_db, p_model, p_repo, p_safe, p_render,
                        p_flash, p_cu]
        mocks = [p.start() for p in self.patches]
        (self.m_login, self.m_qedit, self.m_db, self.m_model, self.m_repo,
         self.m_safe, self.m_render, self.m_flash, _) = mocks

        self.m_render.return_value = "rendered"
        self.m_safe.return_value = True
        self.m_repo.get_all.return_value = []

        bp = Blueprint('quality', __name__, url_prefix='/quality')
        from app.routes.quality.environmental import register_routes
        register_routes(bp)
        app.register_blueprint(bp)

        self.client = app.test_client()

        yield

        for p in self.patches:
            p.stop()

    # -- environmental_list --

    def test_environmental_list(self):
        self.m_repo.get_all.return_value = []

        with self.app.app_context():
            resp = self.client.get('/quality/environmental')
        assert resp.status_code == 200
        assert 'quality/environmental_list.html' in self.m_render.call_args[0][0]

    # -- environmental_add within limits --

    def test_environmental_add_within_limits(self):
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': '22.5',
                'humidity': '45.0',
                'temp_min': '15',
                'temp_max': '30',
                'humidity_min': '20',
                'humidity_max': '70',
                'location': 'Lab Room 1',
                'notes': 'Normal conditions',
            })
        assert resp.status_code == 302
        self.m_repo.save.assert_called_once()
        # Check within_limits was True
        call_kwargs = self.m_model.call_args
        assert call_kwargs[1]['within_limits'] is True

    # -- environmental_add outside limits --

    def test_environmental_add_outside_limits(self):
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': '35.0',
                'humidity': '80.0',
                'temp_min': '15',
                'temp_max': '30',
                'humidity_min': '20',
                'humidity_max': '70',
                'location': 'Lab Room 2',
            })
        assert resp.status_code == 302
        call_kwargs = self.m_model.call_args
        assert call_kwargs[1]['within_limits'] is False

    # -- environmental_add temp outside, humidity inside --

    def test_environmental_add_temp_outside_only(self):
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': '5.0',
                'humidity': '50.0',
                'temp_min': '15',
                'temp_max': '30',
                'humidity_min': '20',
                'humidity_max': '70',
            })
        assert resp.status_code == 302
        call_kwargs = self.m_model.call_args
        assert call_kwargs[1]['within_limits'] is False

    # -- environmental_add humidity outside, temp inside --

    def test_environmental_add_humidity_outside_only(self):
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': '22.0',
                'humidity': '10.0',
                'temp_min': '15',
                'temp_max': '30',
                'humidity_min': '20',
                'humidity_max': '70',
            })
        assert resp.status_code == 302
        call_kwargs = self.m_model.call_args
        assert call_kwargs[1]['within_limits'] is False

    # -- environmental_add with default min/max --

    def test_environmental_add_default_limits(self):
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': '22.5',
                'humidity': '45.0',
            })
        assert resp.status_code == 302
        self.m_repo.save.assert_called_once()

    # -- environmental_add invalid float --

    def test_environmental_add_invalid_temperature(self):
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': 'abc',
                'humidity': '45.0',
            })
        assert resp.status_code == 302
        self.m_flash.assert_called()
        # Should not add to session
        self.m_repo.save.assert_not_called()

    # -- environmental_add missing temperature key --

    def test_environmental_add_missing_temperature(self):
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'humidity': '45.0',
            })
        assert resp.status_code == 302
        self.m_repo.save.assert_not_called()

    # -- environmental_add invalid humidity --

    def test_environmental_add_invalid_humidity(self):
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': '22.0',
                'humidity': 'invalid',
            })
        assert resp.status_code == 302
        self.m_repo.save.assert_not_called()

    # -- environmental_add commit failure --

    def test_environmental_add_commit_failure(self):
        self.m_safe.return_value = False
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': '22.0',
                'humidity': '45.0',
            })
        assert resp.status_code == 302

    # -- environmental_add within limits flash success --

    def test_environmental_add_within_limits_flash(self):
        self.m_safe.return_value = True
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': '22.0',
                'humidity': '50.0',
                'temp_min': '15',
                'temp_max': '30',
                'humidity_min': '20',
                'humidity_max': '70',
            })
        # Check success flash
        flash_calls = self.m_flash.call_args_list
        found_success = any('success' in str(c) for c in flash_calls)
        assert found_success

    # -- environmental_add outside limits flash warning --

    def test_environmental_add_outside_limits_flash(self):
        self.m_safe.return_value = True
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': '50.0',
                'humidity': '80.0',
                'temp_min': '15',
                'temp_max': '30',
                'humidity_min': '20',
                'humidity_max': '70',
            })
        flash_calls = self.m_flash.call_args_list
        found_warning = any('warning' in str(c) for c in flash_calls)
        assert found_warning

    # -- environmental_add default location --

    def test_environmental_add_default_location(self):
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': '22.0',
                'humidity': '50.0',
            })
        call_kwargs = self.m_model.call_args[1]
        assert call_kwargs['location'] == 'Sample Storage'

    # -- environmental_add boundary values (exactly at limits) --

    def test_environmental_add_boundary_at_limits(self):
        with self.app.app_context():
            resp = self.client.post('/quality/environmental/add', data={
                'temperature': '15.0',
                'humidity': '20.0',
                'temp_min': '15',
                'temp_max': '30',
                'humidity_min': '20',
                'humidity_max': '70',
            })
        call_kwargs = self.m_model.call_args[1]
        assert call_kwargs['within_limits'] is True


# =========================================================================
# Proficiency tests
# =========================================================================

class TestProficiencyRoutes:
    """Tests for app/routes/quality/proficiency.py"""

    @pytest.fixture(autouse=True)
    def setup(self, app, mock_user):
        self.app = app
        self.mock_user = mock_user

        self.patches = []

        p_login = patch(
            'app.routes.quality.proficiency.login_required', _noop_login_required
        )
        p_qedit = patch(
            'app.routes.quality.proficiency.require_quality_edit', _noop_decorator
        )
        p_db = patch('app.routes.quality.proficiency.db')
        p_model = patch('app.routes.quality.proficiency.ProficiencyTest')
        p_repo = patch('app.routes.quality.proficiency.ProficiencyTestRepository')
        p_safe = patch('app.routes.quality.proficiency.safe_commit')
        p_stats = patch('app.routes.quality.proficiency.calculate_status_stats')
        p_parse_date = patch('app.routes.quality.proficiency.parse_date')
        p_render = patch('app.routes.quality.proficiency.render_template')
        p_flash = patch('app.routes.quality.proficiency.flash')
        p_cu = patch('app.routes.quality.proficiency.current_user', self.mock_user)

        self.patches = [p_login, p_qedit, p_db, p_model, p_repo, p_safe, p_stats,
                        p_parse_date, p_render, p_flash, p_cu]
        mocks = [p.start() for p in self.patches]
        (self.m_login, self.m_qedit, self.m_db, self.m_model, self.m_repo,
         self.m_safe, self.m_stats, self.m_parse_date, self.m_render, self.m_flash, _) = mocks

        self.m_render.return_value = "rendered"
        self.m_safe.return_value = True
        self.m_stats.return_value = {}
        self.m_parse_date.return_value = date(2026, 1, 15)
        self.m_repo.get_all.return_value = []

        bp = Blueprint('quality', __name__, url_prefix='/quality')
        from app.routes.quality.proficiency import register_routes
        register_routes(bp)
        app.register_blueprint(bp)

        self.client = app.test_client()

        yield

        for p in self.patches:
            p.stop()

    # -- proficiency_list --

    def test_proficiency_list(self):
        self.m_repo.get_all.return_value = []

        with self.app.app_context():
            resp = self.client.get('/quality/proficiency')
        assert resp.status_code == 200
        assert 'quality/proficiency_list.html' in self.m_render.call_args[0][0]
        self.m_stats.assert_called_once()

    # -- proficiency_new GET --

    def test_proficiency_new_get(self):
        with self.app.app_context():
            resp = self.client.get('/quality/proficiency/new')
        assert resp.status_code == 200
        assert 'quality/proficiency_form.html' in self.m_render.call_args[0][0]

    # -- proficiency_new POST satisfactory z-score --

    def test_proficiency_new_post_satisfactory(self):
        """Z-score <= 2 => satisfactory"""
        mock_pt = MagicMock()
        mock_pt.pt_program = "PT-2026"
        self.m_model.return_value = mock_pt

        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '10.5',
                'assigned_value': '10.0',
                'uncertainty': '1.0',
                'pt_provider': 'APLAC',
                'pt_program': 'PT-2026',
                'round_number': 'R1',
                'sample_code': 'S001',
                'analysis_code': 'Mad',
                'test_date': '2026-01-15',
                'notes': 'Test note',
            })
        assert resp.status_code == 302
        self.m_repo.save.assert_called_once()
        # z_score = (10.5 - 10.0) / 1.0 = 0.5 => satisfactory
        call_kwargs = self.m_model.call_args[1]
        assert abs(call_kwargs['z_score'] - 0.5) < 0.001
        assert call_kwargs['performance'] == 'satisfactory'

    # -- proficiency_new POST questionable z-score --

    def test_proficiency_new_post_questionable(self):
        """2 < |Z-score| <= 3 => questionable"""
        mock_pt = MagicMock()
        mock_pt.pt_program = "PT-2026"
        self.m_model.return_value = mock_pt

        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '12.5',
                'assigned_value': '10.0',
                'uncertainty': '1.0',
                'pt_provider': 'APLAC',
                'pt_program': 'PT-2026',
                'round_number': 'R1',
                'sample_code': 'S001',
                'analysis_code': 'Mad',
                'test_date': '2026-01-15',
                'notes': '',
            })
        assert resp.status_code == 302
        # z_score = (12.5 - 10.0) / 1.0 = 2.5 => questionable
        call_kwargs = self.m_model.call_args[1]
        assert abs(call_kwargs['z_score'] - 2.5) < 0.001
        assert call_kwargs['performance'] == 'questionable'

    # -- proficiency_new POST unsatisfactory z-score --

    def test_proficiency_new_post_unsatisfactory(self):
        """|Z-score| > 3 => unsatisfactory"""
        mock_pt = MagicMock()
        mock_pt.pt_program = "PT-2026"
        self.m_model.return_value = mock_pt

        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '14.0',
                'assigned_value': '10.0',
                'uncertainty': '1.0',
                'pt_provider': 'APLAC',
                'pt_program': 'PT-2026',
                'round_number': 'R1',
                'sample_code': 'S001',
                'analysis_code': 'Mad',
                'test_date': '2026-01-15',
            })
        assert resp.status_code == 302
        # z_score = (14.0 - 10.0) / 1.0 = 4.0 => unsatisfactory
        call_kwargs = self.m_model.call_args[1]
        assert abs(call_kwargs['z_score'] - 4.0) < 0.001
        assert call_kwargs['performance'] == 'unsatisfactory'

    # -- proficiency_new POST uncertainty zero --

    def test_proficiency_new_post_zero_uncertainty(self):
        """uncertainty == 0 => z_score = 0 => satisfactory"""
        mock_pt = MagicMock()
        mock_pt.pt_program = "PT-2026"
        self.m_model.return_value = mock_pt

        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '10.5',
                'assigned_value': '10.0',
                'uncertainty': '0',
                'pt_provider': 'APLAC',
                'pt_program': 'PT-2026',
                'round_number': 'R1',
                'sample_code': 'S001',
                'analysis_code': 'Mad',
                'test_date': '2026-01-15',
            })
        assert resp.status_code == 302
        call_kwargs = self.m_model.call_args[1]
        assert call_kwargs['z_score'] == 0
        assert call_kwargs['performance'] == 'satisfactory'

    # -- proficiency_new POST invalid float --

    def test_proficiency_new_post_invalid_float(self):
        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': 'not_a_number',
                'assigned_value': '10.0',
                'uncertainty': '1.0',
            })
        assert resp.status_code == 200
        self.m_render.assert_called()
        self.m_flash.assert_called()
        self.m_repo.save.assert_not_called()

    # -- proficiency_new POST invalid assigned_value --

    def test_proficiency_new_post_invalid_assigned_value(self):
        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '10.0',
                'assigned_value': 'xyz',
                'uncertainty': '1.0',
            })
        assert resp.status_code == 200
        self.m_repo.save.assert_not_called()

    # -- proficiency_new POST invalid uncertainty --

    def test_proficiency_new_post_invalid_uncertainty(self):
        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '10.0',
                'assigned_value': '10.0',
                'uncertainty': 'bad',
            })
        assert resp.status_code == 200
        self.m_repo.save.assert_not_called()

    # -- proficiency_new POST commit failure --

    def test_proficiency_new_post_commit_failure(self):
        self.m_safe.return_value = False
        mock_pt = MagicMock()
        mock_pt.pt_program = "PT-2026"
        self.m_model.return_value = mock_pt

        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '10.0',
                'assigned_value': '10.0',
                'uncertainty': '1.0',
                'pt_provider': 'APLAC',
                'pt_program': 'PT-2026',
            })
        # Should render form again (not redirect)
        assert resp.status_code == 200
        self.m_render.assert_called()

    # -- proficiency_new POST negative z-score unsatisfactory --

    def test_proficiency_new_post_negative_unsatisfactory(self):
        """Negative z-score with abs > 3 => unsatisfactory"""
        mock_pt = MagicMock()
        mock_pt.pt_program = "PT-2026"
        self.m_model.return_value = mock_pt

        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '5.0',
                'assigned_value': '10.0',
                'uncertainty': '1.0',
                'pt_provider': 'APLAC',
                'pt_program': 'PT-2026',
                'round_number': 'R1',
                'sample_code': 'S001',
                'analysis_code': 'Mad',
                'test_date': '2026-01-15',
            })
        assert resp.status_code == 302
        # z_score = (5.0 - 10.0) / 1.0 = -5.0 => unsatisfactory
        call_kwargs = self.m_model.call_args[1]
        assert abs(call_kwargs['z_score'] - (-5.0)) < 0.001
        assert call_kwargs['performance'] == 'unsatisfactory'

    # -- proficiency_new POST boundary z-score = 2 exactly --

    def test_proficiency_new_post_zscore_exactly_2(self):
        """Z-score = 2.0 => satisfactory (abs <= 2)"""
        mock_pt = MagicMock()
        mock_pt.pt_program = "PT-2026"
        self.m_model.return_value = mock_pt

        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '12.0',
                'assigned_value': '10.0',
                'uncertainty': '1.0',
                'pt_provider': 'APLAC',
                'pt_program': 'PT-2026',
                'round_number': 'R1',
                'sample_code': 'S001',
                'analysis_code': 'Mad',
                'test_date': '2026-01-15',
            })
        call_kwargs = self.m_model.call_args[1]
        assert abs(call_kwargs['z_score'] - 2.0) < 0.001
        assert call_kwargs['performance'] == 'satisfactory'

    # -- proficiency_new POST boundary z-score = 3 exactly --

    def test_proficiency_new_post_zscore_exactly_3(self):
        """Z-score = 3.0 => questionable (abs <= 3)"""
        mock_pt = MagicMock()
        mock_pt.pt_program = "PT-2026"
        self.m_model.return_value = mock_pt

        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '13.0',
                'assigned_value': '10.0',
                'uncertainty': '1.0',
                'pt_provider': 'APLAC',
                'pt_program': 'PT-2026',
                'round_number': 'R1',
                'sample_code': 'S001',
                'analysis_code': 'Mad',
                'test_date': '2026-01-15',
            })
        call_kwargs = self.m_model.call_args[1]
        assert abs(call_kwargs['z_score'] - 3.0) < 0.001
        assert call_kwargs['performance'] == 'questionable'

    # -- proficiency_new POST success flash message --

    def test_proficiency_new_post_success_flash(self):
        mock_pt = MagicMock()
        mock_pt.pt_program = "PT-2026"
        self.m_model.return_value = mock_pt

        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '10.0',
                'assigned_value': '10.0',
                'uncertainty': '1.0',
                'pt_provider': 'APLAC',
                'pt_program': 'PT-2026',
                'round_number': 'R1',
                'sample_code': 'S001',
                'analysis_code': 'Mad',
                'test_date': '2026-01-15',
            })
        assert resp.status_code == 302
        flash_calls = self.m_flash.call_args_list
        found_success = any('success' in str(c) for c in flash_calls)
        assert found_success

    # -- proficiency_new POST missing form fields defaults --

    def test_proficiency_new_post_missing_optional_fields(self):
        """our_result, assigned_value, uncertainty default to 0 from form.get"""
        mock_pt = MagicMock()
        mock_pt.pt_program = None
        self.m_model.return_value = mock_pt

        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '0',
                'assigned_value': '0',
                'uncertainty': '0',
            })
        assert resp.status_code == 302
        call_kwargs = self.m_model.call_args[1]
        assert call_kwargs['z_score'] == 0
        assert call_kwargs['performance'] == 'satisfactory'

    # -- proficiency_new POST negative uncertainty --

    def test_proficiency_new_post_negative_uncertainty(self):
        """Negative uncertainty is still > 0 in abs, but code checks uncertainty > 0"""
        mock_pt = MagicMock()
        mock_pt.pt_program = "PT-2026"
        self.m_model.return_value = mock_pt

        with self.app.app_context():
            resp = self.client.post('/quality/proficiency/new', data={
                'our_result': '10.0',
                'assigned_value': '10.0',
                'uncertainty': '-1.0',
                'pt_provider': 'APLAC',
                'pt_program': 'PT-2026',
                'round_number': 'R1',
                'sample_code': 'S001',
                'analysis_code': 'Mad',
                'test_date': '2026-01-15',
            })
        assert resp.status_code == 302
        # uncertainty = -1.0, which is NOT > 0, so z_score = 0
        call_kwargs = self.m_model.call_args[1]
        assert call_kwargs['z_score'] == 0
        assert call_kwargs['performance'] == 'satisfactory'
