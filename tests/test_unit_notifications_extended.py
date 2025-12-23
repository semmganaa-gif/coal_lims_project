# -*- coding: utf-8 -*-
"""
Notifications utils extended тестүүд
"""
import pytest


class TestNotificationsModule:
    """Notifications module тестүүд"""

    def test_import_module(self):
        """Module import"""
        from app.utils import notifications
        assert notifications is not None


class TestSendNotification:
    """send_notification тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.notifications import send_notification
        assert send_notification is not None


class TestNotifyQCFailure:
    """notify_qc_failure тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.notifications import notify_qc_failure
        assert notify_qc_failure is not None


class TestNotifySampleStatusChange:
    """notify_sample_status_change тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.notifications import notify_sample_status_change
        assert notify_sample_status_change is not None


class TestNotifyEquipmentCalibrationDue:
    """notify_equipment_calibration_due тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.notifications import notify_equipment_calibration_due
        assert notify_equipment_calibration_due is not None


class TestCheckAndNotifyWestgard:
    """check_and_notify_westgard тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.notifications import check_and_notify_westgard
        assert check_and_notify_westgard is not None


class TestCheckAndSendEquipmentNotifications:
    """check_and_send_equipment_notifications тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.notifications import check_and_send_equipment_notifications
        assert check_and_send_equipment_notifications is not None


class TestGetNotificationRecipients:
    """get_notification_recipients тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.notifications import get_notification_recipients
        assert get_notification_recipients is not None


class TestNotificationTemplates:
    """Notification templates тестүүд"""

    def test_qc_failure_template(self):
        """QC failure template"""
        from app.utils.notifications import QC_FAILURE_TEMPLATE
        assert QC_FAILURE_TEMPLATE is not None

    def test_sample_status_template(self):
        """Sample status template"""
        from app.utils.notifications import SAMPLE_STATUS_TEMPLATE
        assert SAMPLE_STATUS_TEMPLATE is not None

    def test_equipment_calibration_template(self):
        """Equipment calibration template"""
        from app.utils.notifications import EQUIPMENT_CALIBRATION_TEMPLATE
        assert EQUIPMENT_CALIBRATION_TEMPLATE is not None
