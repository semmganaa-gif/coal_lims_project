# tests/test_notifications_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/notifications.py
"""

import pytest
from unittest.mock import patch, MagicMock


class TestGetEmailSignature:
    """Tests for get_email_signature function."""

    def test_returns_string(self, app):
        """Test returns a string."""
        with app.app_context():
            from app.utils.notifications import get_email_signature
            result = get_email_signature()
            assert isinstance(result, str)

    def test_default_signature(self, app):
        """Test default signature when no user."""
        with app.app_context():
            from app.utils.notifications import get_email_signature
            result = get_email_signature(None)
            assert "Laboratory Team" in result

    def test_user_signature(self, app, db):
        """Test signature with user."""
        with app.app_context():
            from app.utils.notifications import get_email_signature
            from app.models import User

            user = User.query.first()
            if user:
                result = get_email_signature(user)
                assert isinstance(result, str)
                assert "ENERGY RESOURCES LLC" in result

    def test_signature_contains_company(self, app):
        """Test signature contains company name."""
        with app.app_context():
            from app.utils.notifications import get_email_signature
            result = get_email_signature()
            assert "ENERGY RESOURCES LLC" in result


class TestGetNotificationRecipients:
    """Tests for get_notification_recipients function."""

    def test_returns_list(self, app, db):
        """Test returns a list."""
        with app.app_context():
            from app.utils.notifications import get_notification_recipients
            result = get_notification_recipients('qc_alert')
            assert isinstance(result, list)

    def test_qc_alert_type(self, app, db):
        """Test QC alert type."""
        with app.app_context():
            from app.utils.notifications import get_notification_recipients
            result = get_notification_recipients('qc_alert')
            assert isinstance(result, list)

    def test_sample_status_type(self, app, db):
        """Test sample status type."""
        with app.app_context():
            from app.utils.notifications import get_notification_recipients
            result = get_notification_recipients('sample_status')
            assert isinstance(result, list)

    def test_equipment_type(self, app, db):
        """Test equipment type."""
        with app.app_context():
            from app.utils.notifications import get_notification_recipients
            result = get_notification_recipients('equipment')
            assert isinstance(result, list)

    def test_with_system_setting(self, app, db):
        """Test with system setting recipients."""
        with app.app_context():
            from app.utils.notifications import get_notification_recipients
            from app.models import SystemSetting

            # Create test setting
            setting = SystemSetting(
                category='notifications',
                key='test_type_recipients',
                value='test@example.com, test2@example.com',
                is_active=True
            )
            db.session.add(setting)
            db.session.commit()

            result = get_notification_recipients('test_type')
            assert 'test@example.com' in result
            assert 'test2@example.com' in result

            # Cleanup
            db.session.delete(setting)
            db.session.commit()


class TestSendNotification:
    """Tests for send_notification function."""

    def test_no_recipients_returns_false(self, app):
        """Test no recipients returns False."""
        with app.app_context():
            from app.utils.notifications import send_notification
            result = send_notification("Test", [], "<p>Test</p>")
            assert result is False

    def test_with_recipients(self, app):
        """Test with recipients (mocked mail)."""
        with app.app_context():
            from app.utils.notifications import send_notification

            with patch('app.utils.notifications.mail.send') as mock_send:
                result = send_notification(
                    "Test Subject",
                    ["test@example.com"],
                    "<p>Test body</p>"
                )
                assert result is True
                mock_send.assert_called_once()

    def test_with_attachments(self, app):
        """Test with attachments."""
        with app.app_context():
            from app.utils.notifications import send_notification

            with patch('app.utils.notifications.mail.send') as mock_send:
                attachments = [{
                    'filename': 'test.txt',
                    'content_type': 'text/plain',
                    'data': b'Test data'
                }]
                result = send_notification(
                    "Test Subject",
                    ["test@example.com"],
                    "<p>Test body</p>",
                    attachments=attachments
                )
                assert result is True

    def test_without_signature(self, app):
        """Test without signature."""
        with app.app_context():
            from app.utils.notifications import send_notification

            with patch('app.utils.notifications.mail.send') as mock_send:
                result = send_notification(
                    "Test Subject",
                    ["test@example.com"],
                    "<p>Test body</p>",
                    include_signature=False
                )
                assert result is True

    def test_mail_exception_returns_false(self, app):
        """Test mail exception returns False."""
        with app.app_context():
            from app.utils.notifications import send_notification

            with patch('app.utils.notifications.mail.send', side_effect=Exception("Mail error")):
                result = send_notification(
                    "Test Subject",
                    ["test@example.com"],
                    "<p>Test body</p>"
                )
                assert result is False


class TestNotifyQcFailure:
    """Tests for notify_qc_failure function."""

    def test_no_recipients_returns_false(self, app, db):
        """Test returns False when no recipients."""
        with app.app_context():
            from app.utils.notifications import notify_qc_failure

            with patch('app.utils.notifications.get_notification_recipients', return_value=[]):
                result = notify_qc_failure(
                    "TS",
                    "QC-001",
                    "reject",
                    ["1:3s"]
                )
                assert result is False

    def test_with_recipients(self, app, db):
        """Test with recipients."""
        with app.app_context():
            from app.utils.notifications import notify_qc_failure

            with patch('app.utils.notifications.get_notification_recipients', return_value=['test@example.com']):
                with patch('app.utils.notifications.send_notification', return_value=True):
                    result = notify_qc_failure(
                        "TS",
                        "QC-001",
                        "reject",
                        ["1:3s", "2:2s"]
                    )
                    assert result is True


class TestNotifySampleStatusChange:
    """Tests for notify_sample_status_change function."""

    def test_no_recipients_returns_false(self, app, db):
        """Test returns False when no recipients."""
        with app.app_context():
            from app.utils.notifications import notify_sample_status_change

            with patch('app.utils.notifications.get_notification_recipients', return_value=[]):
                result = notify_sample_status_change(
                    "SAMPLE-001",
                    "approved",
                    "admin"
                )
                assert result is False

    def test_with_approved_status(self, app, db):
        """Test with approved status."""
        with app.app_context():
            from app.utils.notifications import notify_sample_status_change

            with patch('app.utils.notifications.get_notification_recipients', return_value=['test@example.com']):
                with patch('app.utils.notifications.send_notification', return_value=True):
                    result = notify_sample_status_change(
                        "SAMPLE-001",
                        "approved",
                        "admin",
                        reason="Quality check passed"
                    )
                    assert result is True

    def test_with_rejected_status(self, app, db):
        """Test with rejected status."""
        with app.app_context():
            from app.utils.notifications import notify_sample_status_change

            with patch('app.utils.notifications.get_notification_recipients', return_value=['test@example.com']):
                with patch('app.utils.notifications.send_notification', return_value=True):
                    result = notify_sample_status_change(
                        "SAMPLE-001",
                        "rejected",
                        "admin"
                    )
                    assert result is True

    def test_with_pending_status(self, app, db):
        """Test with pending status."""
        with app.app_context():
            from app.utils.notifications import notify_sample_status_change

            with patch('app.utils.notifications.get_notification_recipients', return_value=['test@example.com']):
                with patch('app.utils.notifications.send_notification', return_value=True):
                    result = notify_sample_status_change(
                        "SAMPLE-001",
                        "pending",
                        "admin"
                    )
                    assert result is True

    def test_with_timestamp(self, app, db):
        """Test with custom timestamp."""
        with app.app_context():
            from app.utils.notifications import notify_sample_status_change

            with patch('app.utils.notifications.get_notification_recipients', return_value=['test@example.com']):
                with patch('app.utils.notifications.send_notification', return_value=True):
                    result = notify_sample_status_change(
                        "SAMPLE-001",
                        "approved",
                        "admin",
                        timestamp="2024-01-15 10:30"
                    )
                    assert result is True


class TestNotifyEquipmentCalibrationDue:
    """Tests for notify_equipment_calibration_due function."""

    def test_empty_list_returns_false(self, app, db):
        """Test empty list returns False."""
        with app.app_context():
            from app.utils.notifications import notify_equipment_calibration_due
            result = notify_equipment_calibration_due([])
            assert result is False

    def test_no_recipients_returns_false(self, app, db):
        """Test no recipients returns False."""
        with app.app_context():
            from app.utils.notifications import notify_equipment_calibration_due

            with patch('app.utils.notifications.get_notification_recipients', return_value=[]):
                result = notify_equipment_calibration_due([
                    {"name": "Balance", "next_calibration": "2024-02-01", "days_left": 10}
                ])
                assert result is False

    def test_with_equipment_list(self, app, db):
        """Test with equipment list."""
        with app.app_context():
            from app.utils.notifications import notify_equipment_calibration_due

            with patch('app.utils.notifications.get_notification_recipients', return_value=['test@example.com']):
                with patch('app.utils.notifications.send_notification', return_value=True):
                    result = notify_equipment_calibration_due([
                        {"name": "Balance", "next_calibration": "2024-02-01", "days_left": 10},
                        {"name": "pH Meter", "next_calibration": "2024-01-25", "days_left": 3}
                    ])
                    assert result is True


class TestCheckAndSendEquipmentNotifications:
    """Tests for check_and_send_equipment_notifications function."""

    def test_no_equipment_due(self, app, db):
        """Test with no equipment due."""
        with app.app_context():
            from app.utils.notifications import check_and_send_equipment_notifications
            # Should not raise error
            check_and_send_equipment_notifications()


class TestCheckAndNotifyWestgard:
    """Tests for check_and_notify_westgard function."""

    def test_no_qc_data(self, app, db):
        """Test with no QC data."""
        with app.app_context():
            from app.utils.notifications import check_and_notify_westgard
            # Should not raise error
            check_and_notify_westgard()


class TestEmailTemplates:
    """Tests for email template constants."""

    def test_qc_failure_template_exists(self, app):
        """Test QC_FAILURE_TEMPLATE exists."""
        with app.app_context():
            from app.utils.notifications import QC_FAILURE_TEMPLATE
            assert isinstance(QC_FAILURE_TEMPLATE, str)
            assert "Westgard" in QC_FAILURE_TEMPLATE

    def test_sample_status_template_exists(self, app):
        """Test SAMPLE_STATUS_TEMPLATE exists."""
        with app.app_context():
            from app.utils.notifications import SAMPLE_STATUS_TEMPLATE
            assert isinstance(SAMPLE_STATUS_TEMPLATE, str)
            assert "статус" in SAMPLE_STATUS_TEMPLATE

    def test_equipment_calibration_template_exists(self, app):
        """Test EQUIPMENT_CALIBRATION_TEMPLATE exists."""
        with app.app_context():
            from app.utils.notifications import EQUIPMENT_CALIBRATION_TEMPLATE
            assert isinstance(EQUIPMENT_CALIBRATION_TEMPLATE, str)
            assert "калибровк" in EQUIPMENT_CALIBRATION_TEMPLATE

    def test_email_signature_template_exists(self, app):
        """Test EMAIL_SIGNATURE_TEMPLATE exists."""
        with app.app_context():
            from app.utils.notifications import EMAIL_SIGNATURE_TEMPLATE
            assert isinstance(EMAIL_SIGNATURE_TEMPLATE, str)
            assert "ENERGY RESOURCES LLC" in EMAIL_SIGNATURE_TEMPLATE
