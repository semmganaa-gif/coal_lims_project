# -*- coding: utf-8 -*-
"""
Notifications utils - бүрэн тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock
from app.utils.notifications import (
    get_notification_recipients,
    send_notification,
    notify_sample_status_change,
    notify_qc_failure,
    notify_equipment_calibration_due,
)


class TestGetNotificationRecipients:
    """Get notification recipients tests"""

    @patch('app.utils.notifications.db')
    def test_get_recipients_qc_alert(self, mock_db):
        """Get recipients for QC alert"""
        mock_exec = MagicMock()
        mock_exec.scalars.return_value.first.return_value = MagicMock(
            value='admin@test.com,senior@test.com'
        )
        mock_db.session.execute.return_value = mock_exec

        result = get_notification_recipients('qc_alert')
        assert isinstance(result, list)
        assert 'admin@test.com' in result
        assert 'senior@test.com' in result

    @patch('app.utils.notifications.db')
    def test_get_recipients_no_setting(self, mock_db):
        """Get recipients when no setting exists"""
        mock_exec1 = MagicMock()
        mock_exec1.scalars.return_value.first.return_value = None
        mock_exec2 = MagicMock()
        mock_exec2.scalars.return_value.all.return_value = []
        mock_db.session.execute.side_effect = [mock_exec1, mock_exec2]

        result = get_notification_recipients('sample_status')
        assert result == [] or isinstance(result, list)

    @patch('app.utils.notifications.db')
    def test_get_recipients_from_users(self, mock_db):
        """Get recipients from admin/senior users when no setting"""
        mock_exec1 = MagicMock()
        mock_exec1.scalars.return_value.first.return_value = None
        mock_admin = MagicMock(email='admin@test.com')
        mock_senior = MagicMock(email='senior@test.com')
        mock_exec2 = MagicMock()
        mock_exec2.scalars.return_value.all.return_value = [mock_admin, mock_senior]
        mock_db.session.execute.side_effect = [mock_exec1, mock_exec2]

        result = get_notification_recipients('equipment')
        assert isinstance(result, list)

    @patch('app.utils.notifications.db')
    def test_get_recipients_empty_value(self, mock_db):
        """Get recipients with empty setting value"""
        mock_exec1 = MagicMock()
        mock_exec1.scalars.return_value.first.return_value = MagicMock(value='')
        mock_exec2 = MagicMock()
        mock_exec2.scalars.return_value.all.return_value = []
        mock_db.session.execute.side_effect = [mock_exec1, mock_exec2]

        result = get_notification_recipients('all')
        assert isinstance(result, list)


class TestSendNotification:
    """Send notification tests"""

    @patch('app.utils.notifications.get_email_signature')
    @patch('app.utils.notifications.Message')
    @patch('app.utils.notifications.mail')
    def test_send_notification_success(self, mock_mail, mock_message, mock_signature):
        """Send notification successfully"""
        mock_msg = MagicMock()
        mock_message.return_value = mock_msg
        mock_signature.return_value = "<p>Signature</p>"

        result = send_notification(
            subject="Test Alert",
            recipients=['test@example.com'],
            html_body="<p>Test</p>"
        )
        assert result is True
        mock_mail.send.assert_called_once_with(mock_msg)

    @patch('app.utils.notifications.mail')
    def test_send_notification_no_recipients(self, mock_mail):
        """Send notification with no recipients"""
        result = send_notification(
            subject="Test",
            recipients=[],
            html_body="<p>Test</p>"
        )
        assert result is False
        mock_mail.send.assert_not_called()

    @patch('app.utils.notifications.get_email_signature')
    @patch('app.utils.notifications.Message')
    @patch('app.utils.notifications.mail')
    def test_send_notification_with_attachments(self, mock_mail, mock_message, mock_signature):
        """Send notification with attachments"""
        mock_msg = MagicMock()
        mock_message.return_value = mock_msg
        mock_signature.return_value = "<p>Signature</p>"

        attachments = [
            {'filename': 'test.pdf', 'content_type': 'application/pdf', 'data': b'test data'}
        ]
        result = send_notification(
            subject="Test with Attachment",
            recipients=['test@example.com'],
            html_body="<p>Test</p>",
            attachments=attachments
        )
        assert result is True
        mock_msg.attach.assert_called_once()

    @patch('app.utils.notifications.get_email_signature')
    @patch('app.utils.notifications.Message')
    @patch('app.utils.notifications.mail')
    def test_send_notification_mail_error(self, mock_mail, mock_message, mock_signature):
        """Send notification handles mail error"""
        mock_msg = MagicMock()
        mock_message.return_value = mock_msg
        mock_signature.return_value = "<p>Signature</p>"
        mock_mail.send.side_effect = OSError("SMTP error")

        result = send_notification(
            subject="Test",
            recipients=['test@example.com'],
            html_body="<p>Test</p>"
        )
        assert result is False

    @patch('app.utils.notifications.get_email_signature')
    @patch('app.utils.notifications.Message')
    @patch('app.utils.notifications.mail')
    def test_send_notification_multiple_recipients(self, mock_mail, mock_message, mock_signature):
        """Send notification to multiple recipients"""
        mock_msg = MagicMock()
        mock_message.return_value = mock_msg
        mock_signature.return_value = "<p>Signature</p>"

        result = send_notification(
            subject="Test Multiple",
            recipients=['test1@example.com', 'test2@example.com', 'test3@example.com'],
            html_body="<p>Test</p>"
        )
        assert result is True


class TestNotifySampleStatusChange:
    """Sample status change notification tests"""

    @patch('app.utils.notifications.send_notification')
    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications._render_email')
    def test_notify_status_change_approved(self, mock_render, mock_recipients, mock_send):
        """Notify on sample approval"""
        mock_recipients.return_value = ['admin@test.com']
        mock_render.return_value = '<html>test</html>'
        mock_send.return_value = True

        result = notify_sample_status_change(
            sample_code="TEST_001",
            new_status="approved",
            changed_by="admin"
        )
        assert result is True

    @patch('app.utils.notifications.send_notification')
    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications._render_email')
    def test_notify_status_change_rejected(self, mock_render, mock_recipients, mock_send):
        """Notify on sample rejection with reason"""
        mock_recipients.return_value = ['admin@test.com']
        mock_render.return_value = '<html>test</html>'
        mock_send.return_value = True

        result = notify_sample_status_change(
            sample_code="TEST_001",
            new_status="rejected",
            changed_by="senior",
            reason="Quality issue"
        )
        assert result is True

    @patch('app.utils.notifications.get_notification_recipients')
    def test_notify_status_change_no_recipients(self, mock_recipients):
        """Notify returns False when no recipients"""
        mock_recipients.return_value = []

        result = notify_sample_status_change(
            sample_code="TEST_001",
            new_status="pending",
            changed_by="analyst"
        )
        assert result is False

    @patch('app.utils.notifications.send_notification')
    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications._render_email')
    def test_notify_status_with_timestamp(self, mock_render, mock_recipients, mock_send):
        """Notify with custom timestamp"""
        mock_recipients.return_value = ['admin@test.com']
        mock_render.return_value = '<html>test</html>'
        mock_send.return_value = True

        result = notify_sample_status_change(
            sample_code="TEST_002",
            new_status="approved",
            changed_by="admin",
            timestamp="2024-12-18 10:30"
        )
        assert result is True

    @patch('app.utils.notifications.send_notification')
    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications._render_email')
    def test_notify_status_pending(self, mock_render, mock_recipients, mock_send):
        """Notify on pending status"""
        mock_recipients.return_value = ['admin@test.com']
        mock_render.return_value = '<html>test</html>'
        mock_send.return_value = True

        result = notify_sample_status_change(
            sample_code="TEST_003",
            new_status="pending",
            changed_by="analyst"
        )
        assert result is True

    @patch('app.utils.notifications.send_notification')
    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications._render_email')
    def test_notify_status_unknown(self, mock_render, mock_recipients, mock_send):
        """Notify on unknown status - default icon/color"""
        mock_recipients.return_value = ['admin@test.com']
        mock_render.return_value = '<html>test</html>'
        mock_send.return_value = True

        result = notify_sample_status_change(
            sample_code="TEST_004",
            new_status="unknown_status",
            changed_by="admin"
        )
        assert result is True


class TestNotifyQcFailure:
    """QC failure notification tests"""

    @patch('app.utils.notifications.send_notification')
    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications._render_email')
    def test_notify_qc_failure(self, mock_render, mock_recipients, mock_send):
        """Notify on QC failure"""
        mock_recipients.return_value = ['admin@test.com']
        mock_render.return_value = '<html>test</html>'
        mock_send.return_value = True

        result = notify_qc_failure(
            analysis_code="TS",
            qc_sample="CM_20241218A",
            status="fail",
            rules_violated=["1:2s", "2:2s"]
        )
        assert result is True

    @patch('app.utils.notifications.send_notification')
    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications._render_email')
    def test_notify_qc_failure_warn(self, mock_render, mock_recipients, mock_send):
        """Notify on QC warning"""
        mock_recipients.return_value = ['admin@test.com']
        mock_render.return_value = '<html>test</html>'
        mock_send.return_value = True

        result = notify_qc_failure(
            analysis_code="CV",
            qc_sample="GBW_20241218A",
            status="warn",
            rules_violated=["1:2s"]
        )
        assert result is True

    @patch('app.utils.notifications.get_notification_recipients')
    def test_notify_qc_failure_no_recipients(self, mock_recipients):
        """Notify QC failure returns False when no recipients"""
        mock_recipients.return_value = []

        result = notify_qc_failure(
            analysis_code="ASH",
            qc_sample="CM_TEST",
            status="reject",
            rules_violated=["10x"]
        )
        assert result is False

    @patch('app.utils.notifications.send_notification')
    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications._render_email')
    def test_notify_qc_failure_multiple_rules(self, mock_render, mock_recipients, mock_send):
        """Notify on QC failure with multiple rule violations"""
        mock_recipients.return_value = ['admin@test.com']
        mock_render.return_value = '<html>test</html>'
        mock_send.return_value = True

        result = notify_qc_failure(
            analysis_code="VM",
            qc_sample="CM_20241218B",
            status="reject",
            rules_violated=["1:3s", "2:2s", "R:4s", "4:1s"]
        )
        assert result is True


class TestNotifyEquipmentCalibrationDue:
    """Equipment calibration notification tests"""

    @patch('app.utils.notifications.send_notification')
    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications._render_email')
    def test_notify_equipment_calibration(self, mock_render, mock_recipients, mock_send):
        """Notify equipment calibration due"""
        mock_recipients.return_value = ['admin@test.com']
        mock_render.return_value = '<html>test</html>'
        mock_send.return_value = True

        equipment_list = [
            {'name': 'Scale-001', 'next_calibration': '2024-12-25', 'days_left': 7},
            {'name': 'Oven-002', 'next_calibration': '2024-12-30', 'days_left': 12}
        ]
        result = notify_equipment_calibration_due(equipment_list)
        assert result is True

    def test_notify_equipment_empty_list(self):
        """Notify returns False for empty equipment list"""
        result = notify_equipment_calibration_due([])
        assert result is False

    @patch('app.utils.notifications.get_notification_recipients')
    def test_notify_equipment_no_recipients(self, mock_recipients):
        """Notify equipment returns False when no recipients"""
        mock_recipients.return_value = []

        equipment_list = [
            {'name': 'Scale-001', 'next_calibration': '2024-12-25', 'days_left': 7}
        ]
        result = notify_equipment_calibration_due(equipment_list)
        assert result is False

    @patch('app.utils.notifications.send_notification')
    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications._render_email')
    def test_notify_equipment_urgent(self, mock_render, mock_recipients, mock_send):
        """Notify equipment with urgent items"""
        mock_recipients.return_value = ['admin@test.com']
        mock_render.return_value = '<html>test</html>'
        mock_send.return_value = True

        equipment_list = [
            {'name': 'Scale-001', 'next_calibration': '2024-12-20', 'days_left': 2},
            {'name': 'Scale-002', 'next_calibration': '2024-12-21', 'days_left': 3}
        ]
        result = notify_equipment_calibration_due(equipment_list)
        assert result is True

    @patch('app.utils.notifications.send_notification')
    @patch('app.utils.notifications.get_notification_recipients')
    @patch('app.utils.notifications._render_email')
    def test_notify_equipment_single_item(self, mock_render, mock_recipients, mock_send):
        """Notify equipment with single item"""
        mock_recipients.return_value = ['admin@test.com']
        mock_render.return_value = '<html>test</html>'
        mock_send.return_value = True

        equipment_list = [
            {'name': 'Furnace-001', 'next_calibration': '2024-12-28', 'days_left': 10}
        ]
        result = notify_equipment_calibration_due(equipment_list)
        assert result is True
