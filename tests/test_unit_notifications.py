# tests/unit/test_notifications.py
# -*- coding: utf-8 -*-
"""
Notification System тест

Tests for email notification functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


class TestGetNotificationRecipients:
    """get_notification_recipients() функцийн тест"""

    def _mock_db_execute(self, results_sequence):
        """Helper: mock db.session.execute to return results in order."""
        mock_db = MagicMock()
        side_effects = []
        for result in results_sequence:
            mock_exec = MagicMock()
            mock_exec.scalars.return_value.first.return_value = result
            mock_exec.scalars.return_value.all.return_value = result if isinstance(result, list) else [result] if result else []
            side_effects.append(mock_exec)
        mock_db.session.execute.side_effect = side_effects
        return mock_db

    def test_recipients_from_system_setting(self, app):
        """SystemSetting-ээс хүлээн авагчдыг авах"""
        from app.utils.notifications import get_notification_recipients

        mock_setting = Mock()
        mock_setting.value = "admin@test.com, senior@test.com"

        with app.app_context():
            with patch('app.utils.notifications.db') as mock_db:
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.first.return_value = mock_setting
                mock_db.session.execute.return_value = mock_exec
                result = get_notification_recipients('qc_alert')

                assert result == ['admin@test.com', 'senior@test.com']

    def test_recipients_empty_setting(self, app):
        """Хоосон SystemSetting үед default ашиглах"""
        from app.utils.notifications import get_notification_recipients

        mock_setting = Mock()
        mock_setting.value = ""

        mock_admin = Mock(email="admin@test.com")
        mock_senior = Mock(email="senior@test.com")

        with app.app_context():
            with patch('app.utils.notifications.db') as mock_db:
                # First call: select(SystemSetting) -> empty setting
                mock_exec1 = MagicMock()
                mock_exec1.scalars.return_value.first.return_value = mock_setting
                # Second call: select(User) -> admin users
                mock_exec2 = MagicMock()
                mock_exec2.scalars.return_value.all.return_value = [mock_admin, mock_senior]
                mock_db.session.execute.side_effect = [mock_exec1, mock_exec2]

                result = get_notification_recipients('sample_status')
                assert 'admin@test.com' in result
                assert 'senior@test.com' in result

    def test_recipients_no_setting(self, app):
        """SystemSetting байхгүй үед default"""
        from app.utils.notifications import get_notification_recipients

        mock_user = Mock(email="default@test.com")

        with app.app_context():
            with patch('app.utils.notifications.db') as mock_db:
                # First call: select(SystemSetting) -> None
                mock_exec1 = MagicMock()
                mock_exec1.scalars.return_value.first.return_value = None
                # Second call: select(User) -> default user
                mock_exec2 = MagicMock()
                mock_exec2.scalars.return_value.all.return_value = [mock_user]
                mock_db.session.execute.side_effect = [mock_exec1, mock_exec2]

                result = get_notification_recipients('equipment')
                assert result == ['default@test.com']

    def test_recipients_filters_empty_emails(self, app):
        """Хоосон email-г шүүх"""
        from app.utils.notifications import get_notification_recipients

        mock_setting = Mock()
        mock_setting.value = "valid@test.com, , blank@test.com, "

        with app.app_context():
            with patch('app.utils.notifications.db') as mock_db:
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.first.return_value = mock_setting
                mock_db.session.execute.return_value = mock_exec
                result = get_notification_recipients('qc_alert')

                assert result == ['valid@test.com', 'blank@test.com']


class TestSendNotification:
    """send_notification() функцийн тест"""

    def test_send_notification_success(self, app):
        """Амжилттай илгээх"""
        from app.utils.notifications import send_notification

        with app.app_context():
            with patch('app.utils.notifications.mail') as mock_mail:
                result = send_notification(
                    subject="Test Subject",
                    recipients=["test@test.com"],
                    html_body="<p>Test content</p>"
                )

                assert result is True
                mock_mail.send.assert_called_once()

    def test_send_notification_no_recipients(self, app):
        """Хүлээн авагчгүй үед"""
        from app.utils.notifications import send_notification

        with app.app_context():
            result = send_notification(
                subject="Test",
                recipients=[],
                html_body="<p>Test</p>"
            )

            assert result is False

    def test_send_notification_with_attachments(self, app):
        """Хавсралттай илгээх"""
        from app.utils.notifications import send_notification

        attachments = [
            {"filename": "report.xlsx", "content_type": "application/xlsx", "data": b"data"}
        ]

        with app.app_context():
            with patch('app.utils.notifications.mail') as mock_mail:
                with patch('app.utils.notifications.Message') as MockMessage:
                    mock_msg = Mock()
                    MockMessage.return_value = mock_msg

                    result = send_notification(
                        subject="Test",
                        recipients=["test@test.com"],
                        html_body="<p>Test</p>",
                        attachments=attachments
                    )

                    assert result is True
                    mock_msg.attach.assert_called_once()

    def test_send_notification_mail_error(self, app):
        """Mail илгээхэд алдаа"""
        from app.utils.notifications import send_notification

        with app.app_context():
            with patch('app.utils.notifications.mail') as mock_mail:
                mock_mail.send.side_effect = OSError("SMTP Error")

                result = send_notification(
                    subject="Test",
                    recipients=["test@test.com"],
                    html_body="<p>Test</p>"
                )

                assert result is False


class TestNotifyQcFailure:
    """notify_qc_failure() функцийн тест"""

    def test_notify_qc_failure_success(self, app):
        """QC alert амжилттай илгээх"""
        from app.utils.notifications import notify_qc_failure

        with app.app_context():
            with patch('app.utils.notifications.get_notification_recipients') as mock_recipients:
                with patch('app.utils.notifications.send_notification') as mock_send:
                    mock_recipients.return_value = ['lab@test.com']
                    mock_send.return_value = True

                    result = notify_qc_failure(
                        analysis_code='Aad',
                        qc_sample='GBW-001',
                        status='reject',
                        rules_violated=['1-3s', '2-2s']
                    )

                    assert result is True
                    mock_send.assert_called_once()
                    call_args = mock_send.call_args
                    assert 'QC Alert' in call_args[1]['subject']

    def test_notify_qc_failure_no_recipients(self, app):
        """Хүлээн авагчгүй үед"""
        from app.utils.notifications import notify_qc_failure

        with app.app_context():
            with patch('app.utils.notifications.get_notification_recipients') as mock_recipients:
                mock_recipients.return_value = []

                result = notify_qc_failure(
                    analysis_code='Mad',
                    qc_sample='GBW-002',
                    status='warning',
                    rules_violated=['1-2s']
                )

                assert result is False


class TestNotifySampleStatusChange:
    """notify_sample_status_change() функцийн тест"""

    def test_notify_sample_approved(self, app):
        """Sample approved мэдэгдэл"""
        from app.utils.notifications import notify_sample_status_change

        with app.app_context():
            with patch('app.utils.notifications.get_notification_recipients') as mock_recipients:
                with patch('app.utils.notifications.send_notification') as mock_send:
                    with patch('app.utils.datetime.now_local') as mock_now:
                        mock_recipients.return_value = ['manager@test.com']
                        mock_send.return_value = True
                        mock_now.return_value = datetime(2025, 12, 11, 10, 30)

                        result = notify_sample_status_change(
                            sample_code='TT-D1',
                            new_status='approved',
                            changed_by='chemist1',
                            reason='QC passed'
                        )

                        assert result is True
                        mock_send.assert_called_once()

    def test_notify_sample_rejected(self, app):
        """Sample rejected мэдэгдэл"""
        from app.utils.notifications import notify_sample_status_change

        with app.app_context():
            with patch('app.utils.notifications.get_notification_recipients') as mock_recipients:
                with patch('app.utils.notifications.send_notification') as mock_send:
                    mock_recipients.return_value = ['manager@test.com']
                    mock_send.return_value = True

                    result = notify_sample_status_change(
                        sample_code='TT-D2',
                        new_status='rejected',
                        changed_by='senior1',
                        reason='QC failed',
                        timestamp='2025-12-11 10:00'
                    )

                    assert result is True

    def test_notify_sample_no_recipients(self, app):
        """Хүлээн авагчгүй үед"""
        from app.utils.notifications import notify_sample_status_change

        with app.app_context():
            with patch('app.utils.notifications.get_notification_recipients') as mock_recipients:
                mock_recipients.return_value = []

                result = notify_sample_status_change(
                    sample_code='TT-D3',
                    new_status='pending',
                    changed_by='prep1'
                )

                assert result is False

    def test_notify_sample_unknown_status(self, app):
        """Unknown status - default color/icon"""
        from app.utils.notifications import notify_sample_status_change

        with app.app_context():
            with patch('app.utils.notifications.get_notification_recipients') as mock_recipients:
                with patch('app.utils.notifications.send_notification') as mock_send:
                    with patch('app.utils.datetime.now_local') as mock_now:
                        mock_recipients.return_value = ['test@test.com']
                        mock_send.return_value = True
                        mock_now.return_value = datetime(2025, 12, 11)

                        result = notify_sample_status_change(
                            sample_code='TT-D4',
                            new_status='custom_status',  # Unknown status
                            changed_by='admin'
                        )

                        assert result is True


class TestNotifyEquipmentCalibrationDue:
    """notify_equipment_calibration_due() функцийн тест"""

    def test_notify_equipment_success(self, app):
        """Equipment мэдэгдэл амжилттай"""
        from app.utils.notifications import notify_equipment_calibration_due

        equipment_list = [
            {'name': 'Balance A', 'next_calibration': '2025-12-15', 'days_left': 4},
            {'name': 'Oven B', 'next_calibration': '2025-12-20', 'days_left': 9},
        ]

        with app.app_context():
            with patch('app.utils.notifications.get_notification_recipients') as mock_recipients:
                with patch('app.utils.notifications.send_notification') as mock_send:
                    mock_recipients.return_value = ['maintenance@test.com']
                    mock_send.return_value = True

                    result = notify_equipment_calibration_due(equipment_list)

                    assert result is True
                    call_args = mock_send.call_args
                    assert '1 urgent' in call_args[1]['subject']  # 1 equipment with <=7 days

    def test_notify_equipment_empty_list(self, app):
        """Хоосон equipment list"""
        from app.utils.notifications import notify_equipment_calibration_due

        result = notify_equipment_calibration_due([])
        assert result is False

    def test_notify_equipment_no_recipients(self, app):
        """Хүлээн авагчгүй үед"""
        from app.utils.notifications import notify_equipment_calibration_due

        equipment_list = [
            {'name': 'Balance A', 'next_calibration': '2025-12-15', 'days_left': 4}
        ]

        with app.app_context():
            with patch('app.utils.notifications.get_notification_recipients') as mock_recipients:
                mock_recipients.return_value = []

                result = notify_equipment_calibration_due(equipment_list)
                assert result is False


class TestCheckAndSendEquipmentNotifications:
    """check_and_send_equipment_notifications() функцийн тест"""

    def test_function_exists(self):
        """Function import хийж чадаж байгаа эсэх"""
        from app.utils.notifications import check_and_send_equipment_notifications
        assert callable(check_and_send_equipment_notifications)

    def test_equipment_list_build_logic(self):
        """Equipment list бүтээх логик"""
        from datetime import date
        # Test the list building logic
        today = date(2025, 12, 11)
        next_cal = date(2025, 12, 21)
        days_left = (next_cal - today).days
        assert days_left == 10

        # Test list structure
        equipment_list = [{
            'name': 'Test Equipment',
            'next_calibration': next_cal.strftime('%Y-%m-%d'),
            'days_left': days_left
        }]
        assert equipment_list[0]['name'] == 'Test Equipment'
        assert equipment_list[0]['days_left'] == 10


class TestCheckAndNotifyWestgard:
    """check_and_notify_westgard() функцийн тест"""

    def test_westgard_check_with_violations(self, app):
        """Westgard зөрчилтэй үед мэдэгдэл"""
        from app.utils.notifications import check_and_notify_westgard

        mock_chart = Mock()
        mock_chart.analysis_code = 'Aad'
        mock_chart.qc_sample_name = 'GBW-001'
        mock_chart.measured_value = 10.5
        mock_chart.target_value = 10.0
        mock_chart.ucl = 12.0
        mock_chart.measurement_date = datetime.now()

        with app.app_context():
            with patch('app.utils.notifications.db') as mock_db:
                with patch('app.utils.westgard.check_westgard_rules') as mock_westgard:
                    with patch('app.utils.westgard.get_qc_status') as mock_status:
                        with patch('app.utils.notifications.notify_qc_failure') as mock_notify:
                            mock_db.session.query.return_value.distinct.return_value.all.return_value = [
                                ('Aad', 'GBW-001')
                            ]
                            # db.session.execute for select(QCControlChart)
                            mock_exec = MagicMock()
                            mock_exec.scalars.return_value.all.return_value = [mock_chart] * 5
                            mock_db.session.execute.return_value = mock_exec
                            mock_westgard.return_value = {'1-3s': True}
                            mock_status.return_value = {'status': 'reject', 'rules_violated': ['1-3s']}

                            check_and_notify_westgard()

                            mock_notify.assert_called_once()

    def test_westgard_check_no_violations(self, app):
        """Westgard зөрчилгүй үед"""
        from app.utils.notifications import check_and_notify_westgard

        mock_chart = Mock()
        mock_chart.analysis_code = 'Mad'
        mock_chart.qc_sample_name = 'GBW-002'
        mock_chart.measured_value = 5.0
        mock_chart.target_value = 5.0
        mock_chart.ucl = 7.0
        mock_chart.measurement_date = datetime.now()

        with app.app_context():
            with patch('app.utils.notifications.db') as mock_db:
                with patch('app.utils.westgard.check_westgard_rules') as mock_westgard:
                    with patch('app.utils.westgard.get_qc_status') as mock_status:
                        with patch('app.utils.notifications.notify_qc_failure') as mock_notify:
                            mock_db.session.query.return_value.distinct.return_value.all.return_value = [
                                ('Mad', 'GBW-002')
                            ]
                            mock_exec = MagicMock()
                            mock_exec.scalars.return_value.all.return_value = [mock_chart] * 5
                            mock_db.session.execute.return_value = mock_exec
                            mock_westgard.return_value = {}
                            mock_status.return_value = {'status': 'ok'}

                            check_and_notify_westgard()

                            mock_notify.assert_not_called()

    def test_westgard_check_insufficient_data(self, app):
        """Хангалттай data байхгүй үед"""
        from app.utils.notifications import check_and_notify_westgard

        mock_chart = Mock()
        mock_chart.analysis_code = 'Vad'
        mock_chart.qc_sample_name = 'GBW-003'

        with app.app_context():
            with patch('app.utils.notifications.db') as mock_db:
                with patch('app.utils.notifications.notify_qc_failure') as mock_notify:
                    mock_db.session.query.return_value.distinct.return_value.all.return_value = [
                        ('Vad', 'GBW-003')
                    ]
                    # Only 1 chart - insufficient
                    mock_exec = MagicMock()
                    mock_exec.scalars.return_value.all.return_value = [mock_chart]
                    mock_db.session.execute.return_value = mock_exec

                    check_and_notify_westgard()

                    mock_notify.assert_not_called()

    def test_westgard_check_empty_analysis_code(self, app):
        """Хоосон analysis_code skip хийх"""
        from app.utils.notifications import check_and_notify_westgard

        with app.app_context():
            with patch('app.utils.notifications.db') as mock_db:
                with patch('app.utils.notifications.notify_qc_failure') as mock_notify:
                    mock_db.session.query.return_value.distinct.return_value.all.return_value = [
                        (None, 'GBW-001'),  # None analysis_code
                        ('Aad', None),       # None qc_sample
                    ]

                    check_and_notify_westgard()

                    mock_notify.assert_not_called()


class TestEmailTemplates:
    """Email template тест"""

    def test_qc_failure_template_exists(self):
        """QC failure template"""
        from app.utils.notifications import QC_FAILURE_TEMPLATE
        assert 'QC Westgard Alert' in QC_FAILURE_TEMPLATE
        assert '{{ analysis_code }}' in QC_FAILURE_TEMPLATE
        assert '{{ qc_sample }}' in QC_FAILURE_TEMPLATE

    def test_sample_status_template_exists(self):
        """Sample status template"""
        from app.utils.notifications import SAMPLE_STATUS_TEMPLATE
        assert '{{ sample_code }}' in SAMPLE_STATUS_TEMPLATE
        assert '{{ new_status }}' in SAMPLE_STATUS_TEMPLATE
        assert '{{ changed_by }}' in SAMPLE_STATUS_TEMPLATE

    def test_equipment_calibration_template_exists(self):
        """Equipment calibration template"""
        from app.utils.notifications import EQUIPMENT_CALIBRATION_TEMPLATE
        assert 'equipment_list' in EQUIPMENT_CALIBRATION_TEMPLATE
        assert 'days_left' in EQUIPMENT_CALIBRATION_TEMPLATE
