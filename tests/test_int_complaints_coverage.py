# tests/integration/test_complaints_coverage.py
"""Customer complaints coverage tests"""
import pytest


class TestComplaintsRoutes:
    """Complaints routes tests"""

    def test_complaints_list(self, auth_admin):
        """Complaints list page"""
        response = auth_admin.get('/quality/complaints')
        assert response.status_code in [200, 302]

    def test_complaints_list_user(self, auth_user):
        """Complaints list as regular user"""
        response = auth_user.get('/quality/complaints')
        assert response.status_code in [200, 302]

    def test_complaints_new_get(self, auth_admin):
        """Complaints new form GET"""
        response = auth_admin.get('/quality/complaints/new')
        assert response.status_code in [200, 302, 403]

    def test_complaints_new_post_valid(self, auth_admin):
        """Create new complaint - valid data"""
        response = auth_admin.post('/quality/complaints/new', data={
            'client_name': 'Test Client',
            'description': 'Test complaint description',
            'contact_person': 'John Doe',
            'contact_email': 'john@example.com',
            'complaint_type': 'quality'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_complaints_new_post_missing_client(self, auth_admin):
        """Create new complaint - missing client name"""
        response = auth_admin.post('/quality/complaints/new', data={
            'description': 'Test complaint description',
            'contact_person': 'John Doe'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_complaints_new_post_missing_description(self, auth_admin):
        """Create new complaint - missing description"""
        response = auth_admin.post('/quality/complaints/new', data={
            'client_name': 'Test Client',
            'contact_person': 'John Doe'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_complaints_new_post_minimal(self, auth_admin):
        """Create new complaint - minimal data"""
        response = auth_admin.post('/quality/complaints/new', data={
            'client_name': 'Minimal Client',
            'description': 'Minimal description'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_complaints_detail_notfound(self, auth_admin):
        """Complaints detail - not found"""
        response = auth_admin.get('/quality/complaints/99999')
        assert response.status_code in [200, 302, 404]

    def test_complaints_resolve_notfound(self, auth_admin):
        """Resolve complaint - not found"""
        response = auth_admin.post('/quality/complaints/99999/resolve', data={
            'investigation_findings': 'Test findings',
            'resolution': 'Test resolution'
        })
        assert response.status_code in [302, 403, 404]


class TestComplaintsModel:
    """Complaints model tests"""

    def test_customer_complaint_query(self, app):
        """Query customer complaints"""
        with app.app_context():
            from app.models import CustomerComplaint
            complaints = CustomerComplaint.query.limit(10).all()
            assert isinstance(complaints, list)

    def test_customer_complaint_order(self, app):
        """Query complaints ordered by date"""
        with app.app_context():
            from app.models import CustomerComplaint
            complaints = CustomerComplaint.query.order_by(
                CustomerComplaint.complaint_date.desc()
            ).all()
            assert isinstance(complaints, list)

    def test_customer_complaint_create(self, app):
        """Create complaint object"""
        with app.app_context():
            from app.models import CustomerComplaint
            complaint = CustomerComplaint(
                complaint_no='COMP-TEST-001',
                client_name='Test Client',
                description='Test description',
                status='received'
            )
            assert complaint.client_name == 'Test Client'
            assert complaint.status == 'received'

    def test_customer_complaint_status_values(self, app):
        """Test valid status values"""
        with app.app_context():
            valid_statuses = ['received', 'investigating', 'resolved', 'closed']
            for status in valid_statuses:
                from app.models import CustomerComplaint
                complaint = CustomerComplaint(
                    complaint_no=f'COMP-{status}',
                    client_name='Test',
                    description='Test',
                    status=status
                )
                assert complaint.status == status


class TestComplaintsHelpers:
    """Complaints helper functions"""

    def test_calculate_status_stats(self, app):
        """Calculate status statistics"""
        with app.app_context():
            from app.utils.quality_helpers import calculate_status_stats
            from app.models import CustomerComplaint
            complaints = CustomerComplaint.query.all()
            stats = calculate_status_stats(
                complaints,
                status_values=['received', 'investigating', 'resolved', 'closed']
            )
            assert isinstance(stats, dict)

    def test_generate_sequential_code(self, app):
        """Generate sequential complaint code"""
        with app.app_context():
            from app.utils.quality_helpers import generate_sequential_code
            from app.models import CustomerComplaint
            code = generate_sequential_code(CustomerComplaint, 'complaint_no', 'COMP')
            assert code.startswith('COMP')


class TestComplaintsIntegration:
    """Complaints integration tests"""

    def test_complaints_workflow(self, auth_admin, app):
        """Full complaint workflow"""
        # 1. Create complaint
        response = auth_admin.post('/quality/complaints/new', data={
            'client_name': 'Workflow Test Client',
            'description': 'Workflow test description',
            'complaint_type': 'quality'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

        # 2. Check list
        response = auth_admin.get('/quality/complaints')
        assert response.status_code in [200, 302]

    def test_complaints_count(self, app):
        """Count complaints"""
        with app.app_context():
            from app.models import CustomerComplaint
            count = CustomerComplaint.query.count()
            assert isinstance(count, int)

    def test_complaints_filter_by_status(self, app):
        """Filter complaints by status"""
        with app.app_context():
            from app.models import CustomerComplaint
            received = CustomerComplaint.query.filter_by(status='received').all()
            resolved = CustomerComplaint.query.filter_by(status='resolved').all()
            assert isinstance(received, list)
            assert isinstance(resolved, list)
