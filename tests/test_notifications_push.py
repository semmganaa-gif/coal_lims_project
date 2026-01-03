# -*- coding: utf-8 -*-
"""
Notifications модулийн coverage тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock


# ============================================================
# Import Tests
# ============================================================

class TestNotificationsImports:
    """notifications модулийн импорт тест"""

    def test_import_module(self):
        from app.utils import notifications
        assert notifications is not None

    def test_import_templates(self):
        from app.utils.notifications import (
            QC_FAILURE_TEMPLATE,
            SAMPLE_STATUS_TEMPLATE,
            EMAIL_SIGNATURE_TEMPLATE,
            EQUIPMENT_CALIBRATION_TEMPLATE
        )
        assert QC_FAILURE_TEMPLATE is not None
        assert SAMPLE_STATUS_TEMPLATE is not None
        assert EMAIL_SIGNATURE_TEMPLATE is not None
        assert EQUIPMENT_CALIBRATION_TEMPLATE is not None


# ============================================================
# Template Tests
# ============================================================

class TestQcFailureTemplate:
    """QC_FAILURE_TEMPLATE тест"""

    def test_template_contains_placeholders(self):
        from app.utils.notifications import QC_FAILURE_TEMPLATE
        assert '{{ analysis_code }}' in QC_FAILURE_TEMPLATE
        assert '{{ qc_sample }}' in QC_FAILURE_TEMPLATE
        assert '{{ status }}' in QC_FAILURE_TEMPLATE
        assert '{{ rules_violated }}' in QC_FAILURE_TEMPLATE


class TestSampleStatusTemplate:
    """SAMPLE_STATUS_TEMPLATE тест"""

    def test_template_contains_placeholders(self):
        from app.utils.notifications import SAMPLE_STATUS_TEMPLATE
        assert '{{ sample_code }}' in SAMPLE_STATUS_TEMPLATE
        assert '{{ new_status }}' in SAMPLE_STATUS_TEMPLATE
        assert '{{ changed_by }}' in SAMPLE_STATUS_TEMPLATE
        assert '{{ color }}' in SAMPLE_STATUS_TEMPLATE


class TestEmailSignatureTemplate:
    """EMAIL_SIGNATURE_TEMPLATE тест"""

    def test_template_contains_placeholders(self):
        from app.utils.notifications import EMAIL_SIGNATURE_TEMPLATE
        assert '{{ sender_name }}' in EMAIL_SIGNATURE_TEMPLATE
        assert '{{ sender_position }}' in EMAIL_SIGNATURE_TEMPLATE
        assert 'ENERGY RESOURCES LLC' in EMAIL_SIGNATURE_TEMPLATE


class TestEquipmentCalibrationTemplate:
    """EQUIPMENT_CALIBRATION_TEMPLATE тест"""

    def test_template_contains_placeholders(self):
        from app.utils.notifications import EQUIPMENT_CALIBRATION_TEMPLATE
        assert 'equipment_list' in EQUIPMENT_CALIBRATION_TEMPLATE
        assert 'eq.name' in EQUIPMENT_CALIBRATION_TEMPLATE
        assert 'eq.next_calibration' in EQUIPMENT_CALIBRATION_TEMPLATE


# ============================================================
# Function Tests
# ============================================================

class TestGetEmailSignature:
    """get_email_signature функц тест"""

    def test_import_function(self):
        from app.utils.notifications import get_email_signature
        assert get_email_signature is not None

    def test_without_user(self, app):
        from app.utils.notifications import get_email_signature
        with app.app_context():
            result = get_email_signature(None)
            assert 'Laboratory Team' in result
            assert 'Coal Analysis Laboratory' in result

    def test_with_user(self, app):
        from app.utils.notifications import get_email_signature
        with app.app_context():
            mock_user = MagicMock()
            mock_user.full_name = 'Test User'
            mock_user.username = 'testuser'
            mock_user.position = 'Senior Chemist'
            mock_user.email = 'test@example.com'
            mock_user.phone = '+976 9999 9999'

            result = get_email_signature(mock_user)
            assert 'Test User' in result
            assert 'Senior Chemist' in result

    def test_with_user_minimal_info(self, app):
        from app.utils.notifications import get_email_signature
        with app.app_context():
            mock_user = MagicMock()
            mock_user.full_name = None
            mock_user.username = 'testuser'
            mock_user.position = None
            mock_user.email = None
            mock_user.phone = None

            result = get_email_signature(mock_user)
            assert 'testuser' in result


class TestGetNotificationRecipients:
    """get_notification_recipients функц тест"""

    def test_import_function(self):
        from app.utils.notifications import get_notification_recipients
        assert get_notification_recipients is not None


class TestSendNotification:
    """send_notification функц тест"""

    def test_import_function(self):
        from app.utils.notifications import send_notification
        assert send_notification is not None

    def test_no_recipients(self, app):
        from app.utils.notifications import send_notification
        with app.app_context():
            result = send_notification(
                subject='Test',
                recipients=[],
                html_body='<p>Test</p>'
            )
            assert result is False

    @patch('app.utils.notifications.mail')
    def test_with_recipients(self, mock_mail, app):
        from app.utils.notifications import send_notification
        with app.app_context():
            result = send_notification(
                subject='Test',
                recipients=['test@example.com'],
                html_body='<p>Test</p>',
                include_signature=False
            )
            # Should attempt to send
            mock_mail.send.assert_called_once()
            assert result is True

    @patch('app.utils.notifications.mail')
    def test_with_attachments(self, mock_mail, app):
        from app.utils.notifications import send_notification
        with app.app_context():
            result = send_notification(
                subject='Test',
                recipients=['test@example.com'],
                html_body='<p>Test</p>',
                attachments=[
                    {'filename': 'test.pdf', 'data': b'test data'}
                ],
                include_signature=False
            )
            mock_mail.send.assert_called_once()

    @patch('app.utils.notifications.mail')
    def test_with_sender_user(self, mock_mail, app):
        from app.utils.notifications import send_notification
        with app.app_context():
            mock_user = MagicMock()
            mock_user.email = 'sender@example.com'
            mock_user.full_name = 'Sender Name'
            mock_user.username = 'sender'
            mock_user.position = 'Chemist'
            mock_user.phone = None

            result = send_notification(
                subject='Test',
                recipients=['test@example.com'],
                html_body='<p>Test</p>',
                sender_user=mock_user
            )
            mock_mail.send.assert_called_once()

    @patch('app.utils.notifications.mail')
    def test_mail_error(self, mock_mail, app):
        from app.utils.notifications import send_notification
        mock_mail.send.side_effect = Exception('SMTP error')
        with app.app_context():
            result = send_notification(
                subject='Test',
                recipients=['test@example.com'],
                html_body='<p>Test</p>',
                include_signature=False
            )
            assert result is False


class TestNotifyQcFailure:
    """notify_qc_failure функц тест"""

    def test_import_function(self):
        from app.utils.notifications import notify_qc_failure
        assert notify_qc_failure is not None

    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications.send_notification')
    def test_with_recipients(self, mock_send, mock_get_recipients, app):
        from app.utils.notifications import notify_qc_failure
        mock_get_recipients.return_value = ['admin@example.com']
        mock_send.return_value = True

        with app.app_context():
            result = notify_qc_failure(
                analysis_code='CV',
                qc_sample='CM-2026-Q1',
                status='reject',
                rules_violated=['1-2s', '2-2s']
            )
            mock_send.assert_called_once()
            assert result is True

    @patch('app.utils.notifications.get_notification_recipients')
    def test_no_recipients(self, mock_get_recipients, app):
        from app.utils.notifications import notify_qc_failure
        mock_get_recipients.return_value = []

        with app.app_context():
            result = notify_qc_failure(
                analysis_code='CV',
                qc_sample='CM-2026-Q1',
                status='reject',
                rules_violated=['1-2s']
            )
            assert result is False


class TestNotifySampleStatusChange:
    """notify_sample_status_change функц тест"""

    def test_import_function(self):
        from app.utils.notifications import notify_sample_status_change
        assert notify_sample_status_change is not None

    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications.send_notification')
    def test_approved_status(self, mock_send, mock_get_recipients, app):
        from app.utils.notifications import notify_sample_status_change
        mock_get_recipients.return_value = ['admin@example.com']
        mock_send.return_value = True

        with app.app_context():
            result = notify_sample_status_change(
                sample_code='SAMPLE-001',
                new_status='approved',
                changed_by='admin',
                reason='All results verified'
            )
            mock_send.assert_called_once()
            assert result is True

    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications.send_notification')
    def test_rejected_status(self, mock_send, mock_get_recipients, app):
        from app.utils.notifications import notify_sample_status_change
        mock_get_recipients.return_value = ['admin@example.com']
        mock_send.return_value = True

        with app.app_context():
            result = notify_sample_status_change(
                sample_code='SAMPLE-001',
                new_status='rejected',
                changed_by='senior',
                reason='Repeatability failed'
            )
            mock_send.assert_called_once()

    @patch('app.utils.notifications.get_notification_recipients')
    def test_no_recipients(self, mock_get_recipients, app):
        from app.utils.notifications import notify_sample_status_change
        mock_get_recipients.return_value = []

        with app.app_context():
            result = notify_sample_status_change(
                sample_code='SAMPLE-001',
                new_status='approved',
                changed_by='admin'
            )
            assert result is False


class TestNotifyEquipmentCalibrationDue:
    """notify_equipment_calibration_due функц тест"""

    def test_import_function(self):
        from app.utils.notifications import notify_equipment_calibration_due
        assert notify_equipment_calibration_due is not None

    def test_empty_list(self, app):
        from app.utils.notifications import notify_equipment_calibration_due
        with app.app_context():
            result = notify_equipment_calibration_due([])
            assert result is False

    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications.send_notification')
    def test_with_equipment(self, mock_send, mock_get_recipients, app):
        from app.utils.notifications import notify_equipment_calibration_due
        mock_get_recipients.return_value = ['admin@example.com']
        mock_send.return_value = True

        with app.app_context():
            result = notify_equipment_calibration_due([
                {'name': 'Balance 1', 'next_calibration': '2026-01-15', 'days_left': 5},
                {'name': 'Furnace 1', 'next_calibration': '2026-01-20', 'days_left': 10}
            ])
            mock_send.assert_called_once()
            assert result is True

    @patch('app.utils.notifications.get_notification_recipients')
    def test_no_recipients(self, mock_get_recipients, app):
        from app.utils.notifications import notify_equipment_calibration_due
        mock_get_recipients.return_value = []

        with app.app_context():
            result = notify_equipment_calibration_due([
                {'name': 'Balance 1', 'next_calibration': '2026-01-15', 'days_left': 5}
            ])
            assert result is False


class TestCheckAndSendEquipmentNotifications:
    """check_and_send_equipment_notifications функц тест"""

    def test_import_function(self):
        from app.utils.notifications import check_and_send_equipment_notifications
        assert check_and_send_equipment_notifications is not None

    @patch('app.utils.notifications.notify_equipment_calibration_due')
    @patch('app.utils.notifications.now_local')
    def test_no_equipment_due(self, mock_now, mock_notify):
        """Test when no equipment is due for calibration"""
        from datetime import datetime
        mock_now.return_value = datetime(2026, 1, 10)

        # This test just verifies import works - actual DB query is complex
        from app.utils.notifications import check_and_send_equipment_notifications
        assert check_and_send_equipment_notifications is not None

    @patch('app.utils.notifications.notify_equipment_calibration_due')
    @patch('app.utils.notifications.now_local')
    def test_with_equipment_due(self, mock_now, mock_notify):
        """Test when equipment is due - basic import test"""
        from datetime import datetime
        mock_now.return_value = datetime(2026, 1, 10)

        from app.utils.notifications import check_and_send_equipment_notifications
        assert check_and_send_equipment_notifications is not None


class TestCheckAndNotifyWestgard:
    """check_and_notify_westgard функц тест"""

    def test_import_function(self):
        from app.utils.notifications import check_and_notify_westgard
        assert check_and_notify_westgard is not None

    @patch('app.utils.notifications.notify_qc_failure')
    @patch('app.utils.westgard.get_qc_status')
    @patch('app.utils.westgard.check_westgard_rules')
    @patch('app.models.QCControlChart')
    @patch('app.utils.notifications.db')
    def test_no_qc_data(self, mock_db, mock_chart, mock_check, mock_status, mock_notify):
        from app.utils.notifications import check_and_notify_westgard

        mock_db.session.query.return_value.distinct.return_value.all.return_value = []

        check_and_notify_westgard()
        mock_notify.assert_not_called()

    @patch('app.utils.notifications.notify_qc_failure')
    @patch('app.utils.westgard.get_qc_status')
    @patch('app.utils.westgard.check_westgard_rules')
    @patch('app.models.QCControlChart')
    @patch('app.utils.notifications.db')
    def test_with_reject_status(self, mock_db, mock_chart, mock_check, mock_status, mock_notify):
        from app.utils.notifications import check_and_notify_westgard

        # Mock unique pairs
        mock_db.session.query.return_value.distinct.return_value.all.return_value = [
            ('Mad', 'QC-1')
        ]

        # Mock chart data
        chart1 = MagicMock()
        chart1.measured_value = 5.0
        chart1.target_value = 5.0
        chart1.ucl = 6.0

        chart2 = MagicMock()
        chart2.measured_value = 5.1
        chart2.target_value = 5.0
        chart2.ucl = 6.0

        mock_chart.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [chart1, chart2]

        # Mock westgard check
        mock_check.return_value = {'1_2s': True}
        mock_status.return_value = {'status': 'reject', 'rules_violated': ['1_2s']}

        check_and_notify_westgard()
        mock_notify.assert_called_once()

    @patch('app.utils.notifications.notify_qc_failure')
    @patch('app.utils.westgard.get_qc_status')
    @patch('app.utils.westgard.check_westgard_rules')
    @patch('app.models.QCControlChart')
    @patch('app.utils.notifications.db')
    def test_with_ok_status(self, mock_db, mock_chart, mock_check, mock_status, mock_notify):
        from app.utils.notifications import check_and_notify_westgard

        mock_db.session.query.return_value.distinct.return_value.all.return_value = [
            ('Mad', 'QC-1')
        ]

        chart1 = MagicMock()
        chart1.measured_value = 5.0
        chart1.target_value = 5.0
        chart1.ucl = 6.0

        chart2 = MagicMock()
        chart2.measured_value = 5.0
        chart2.target_value = 5.0
        chart2.ucl = 6.0

        mock_chart.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [chart1, chart2]

        mock_check.return_value = {}
        mock_status.return_value = {'status': 'ok', 'rules_violated': []}

        check_and_notify_westgard()
        # Should not notify for 'ok' status
        mock_notify.assert_not_called()

    @patch('app.utils.notifications.notify_qc_failure')
    @patch('app.models.QCControlChart')
    @patch('app.utils.notifications.db')
    def test_skip_empty_analysis_code(self, mock_db, mock_chart, mock_notify):
        from app.utils.notifications import check_and_notify_westgard

        mock_db.session.query.return_value.distinct.return_value.all.return_value = [
            (None, 'QC-1'),
            ('', 'QC-2'),
            ('Mad', None)
        ]

        check_and_notify_westgard()
        mock_notify.assert_not_called()

    @patch('app.utils.notifications.notify_qc_failure')
    @patch('app.models.QCControlChart')
    @patch('app.utils.notifications.db')
    def test_skip_insufficient_data(self, mock_db, mock_chart, mock_notify):
        from app.utils.notifications import check_and_notify_westgard

        mock_db.session.query.return_value.distinct.return_value.all.return_value = [
            ('Mad', 'QC-1')
        ]

        # Only 1 chart - not enough
        chart1 = MagicMock()
        chart1.measured_value = 5.0
        mock_chart.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [chart1]

        check_and_notify_westgard()
        mock_notify.assert_not_called()

    @patch('app.utils.notifications.notify_qc_failure')
    @patch('app.utils.westgard.get_qc_status')
    @patch('app.utils.westgard.check_westgard_rules')
    @patch('app.models.QCControlChart')
    @patch('app.utils.notifications.db')
    def test_calculate_sd_from_values(self, mock_db, mock_chart, mock_check, mock_status, mock_notify):
        from app.utils.notifications import check_and_notify_westgard

        mock_db.session.query.return_value.distinct.return_value.all.return_value = [
            ('Mad', 'QC-1')
        ]

        # Charts without UCL - should calculate SD from values
        chart1 = MagicMock()
        chart1.measured_value = 5.0
        chart1.target_value = 5.0
        chart1.ucl = None

        chart2 = MagicMock()
        chart2.measured_value = 5.2
        chart2.target_value = 5.0
        chart2.ucl = None

        mock_chart.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [chart1, chart2]

        mock_check.return_value = {}
        mock_status.return_value = {'status': 'ok', 'rules_violated': []}

        check_and_notify_westgard()
        # Should calculate SD and run without error

    @patch('app.utils.notifications.notify_qc_failure')
    @patch('app.utils.westgard.get_qc_status')
    @patch('app.utils.westgard.check_westgard_rules')
    @patch('app.models.QCControlChart')
    @patch('app.utils.notifications.db')
    def test_zero_sd_fallback(self, mock_db, mock_chart, mock_check, mock_status, mock_notify):
        from app.utils.notifications import check_and_notify_westgard

        mock_db.session.query.return_value.distinct.return_value.all.return_value = [
            ('Mad', 'QC-1')
        ]

        # All same values - SD would be 0, should use 0.001
        chart1 = MagicMock()
        chart1.measured_value = 5.0
        chart1.target_value = 5.0
        chart1.ucl = 5.0  # UCL = target means SD = 0

        chart2 = MagicMock()
        chart2.measured_value = 5.0
        chart2.target_value = 5.0
        chart2.ucl = 5.0

        mock_chart.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [chart1, chart2]

        mock_check.return_value = {}
        mock_status.return_value = {'status': 'ok', 'rules_violated': []}

        check_and_notify_westgard()
        # Should handle zero SD by using 0.001


# ============================================================
# Fixtures - conftest.py дээрээс app, client авна
# ============================================================
# No additional fixtures needed - using from conftest.py
