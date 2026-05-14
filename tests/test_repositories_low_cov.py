# tests/test_repositories_low_cov.py
# -*- coding: utf-8 -*-
"""
Tests for repository files with low coverage:
  - ChatMessageRepository, UserOnlineStatusRepository
  - EquipmentRepository
  - AuditLogRepository
  - LabReportRepository, ReportSignatureRepository
  - MaintenanceLogRepository, UsageLogRepository
  - AnalysisResultRepository
  - SystemSettingRepository
  - ChemicalRepository
  - UserRepository
"""

import uuid
from datetime import date, datetime, timedelta

import pytest

from app import db as _db
from app.models import (
    AnalysisResult,
    AuditLog,
    ChatMessage,
    Chemical,
    Equipment,
    LabReport,
    MaintenanceLog,
    ReportSignature,
    Sample,
    SystemSetting,
    UsageLog,
    User,
    UserOnlineStatus,
)
from app.repositories.analysis_result_repository import AnalysisResultRepository
from app.repositories.audit_repository import AuditLogRepository
from app.repositories.chat_repository import ChatMessageRepository, UserOnlineStatusRepository
from app.repositories.chemical_repository import ChemicalRepository
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.maintenance_repository import MaintenanceLogRepository, UsageLogRepository
from app.repositories.report_repository import LabReportRepository, ReportSignatureRepository
from app.repositories.system_setting_repository import SystemSettingRepository
from app.repositories.user_repository import UserRepository


# =========================================================================
# Helpers
# =========================================================================

def _unique(prefix="T"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _get_user(username="chemist"):
    return User.query.filter_by(username=username).first()


# =========================================================================
# ChatMessageRepository
# =========================================================================

class TestChatMessageRepository:

    def test_save_and_get_by_id(self, app):
        with app.app_context():
            u = _get_user()
            msg = ChatMessage(sender_id=u.id, message="hello")
            saved = ChatMessageRepository.save(msg, commit=True)
            assert saved.id is not None

            fetched = ChatMessageRepository.get_by_id(saved.id)
            assert fetched is not None
            assert fetched.message == "hello"

            # cleanup
            _db.session.delete(fetched)
            _db.session.commit()

    def test_get_by_id_returns_none(self, app):
        with app.app_context():
            assert ChatMessageRepository.get_by_id(999999) is None

    def test_get_conversation(self, app):
        with app.app_context():
            u1 = _get_user("admin")
            u2 = _get_user("chemist")
            m1 = ChatMessage(sender_id=u1.id, receiver_id=u2.id, message="hi")
            m2 = ChatMessage(sender_id=u2.id, receiver_id=u1.id, message="hello")
            m3 = ChatMessage(sender_id=u1.id, receiver_id=u2.id, message="deleted", is_deleted=True)
            _db.session.add_all([m1, m2, m3])
            _db.session.commit()

            convo = ChatMessageRepository.get_conversation(u1.id, u2.id, limit=50)
            msgs = [c.message for c in convo]
            assert "hi" in msgs
            assert "hello" in msgs
            # deleted messages should be excluded
            assert "deleted" not in msgs

            _db.session.delete(m1)
            _db.session.delete(m2)
            _db.session.delete(m3)
            _db.session.commit()

    def test_get_broadcasts(self, app):
        with app.app_context():
            u = _get_user()
            bc = ChatMessage(sender_id=u.id, message="broadcast!", is_broadcast=True)
            _db.session.add(bc)
            _db.session.commit()

            results = ChatMessageRepository.get_broadcasts(limit=10)
            assert any(r.message == "broadcast!" for r in results)

            _db.session.delete(bc)
            _db.session.commit()

    def test_get_unread_count(self, app):
        with app.app_context():
            u1 = _get_user("admin")
            u2 = _get_user("chemist")
            m = ChatMessage(sender_id=u1.id, receiver_id=u2.id, message="unread")
            _db.session.add(m)
            _db.session.commit()

            count = ChatMessageRepository.get_unread_count(u2.id)
            assert count >= 1

            _db.session.delete(m)
            _db.session.commit()

    def test_mark_as_read(self, app):
        with app.app_context():
            u1 = _get_user("admin")
            u2 = _get_user("chemist")
            m = ChatMessage(sender_id=u1.id, receiver_id=u2.id, message="to read")
            _db.session.add(m)
            _db.session.commit()

            updated = ChatMessageRepository.mark_as_read([m.id], commit=True)
            assert updated == 1

            refreshed = ChatMessageRepository.get_by_id(m.id)
            assert refreshed.read_at is not None

            _db.session.delete(refreshed)
            _db.session.commit()

    def test_mark_as_read_already_read(self, app):
        """Already-read messages should not be updated again."""
        with app.app_context():
            u = _get_user()
            m = ChatMessage(sender_id=u.id, receiver_id=u.id, message="already read", read_at=datetime.utcnow())
            _db.session.add(m)
            _db.session.commit()

            updated = ChatMessageRepository.mark_as_read([m.id], commit=True)
            assert updated == 0

            _db.session.delete(m)
            _db.session.commit()

    def test_soft_delete(self, app):
        with app.app_context():
            u = _get_user()
            m = ChatMessage(sender_id=u.id, message="to delete")
            _db.session.add(m)
            _db.session.commit()

            result = ChatMessageRepository.soft_delete(m, commit=True)
            assert result is True
            assert m.is_deleted is True
            assert m.deleted_at is not None

            _db.session.delete(m)
            _db.session.commit()

    def test_save_no_commit(self, app):
        with app.app_context():
            u = _get_user()
            m = ChatMessage(sender_id=u.id, message="no commit")
            ChatMessageRepository.save(m, commit=False)
            _db.session.commit()
            assert m.id is not None
            _db.session.delete(m)
            _db.session.commit()


# =========================================================================
# UserOnlineStatusRepository
# =========================================================================

class TestUserOnlineStatusRepository:

    def test_set_online_new_user(self, app):
        with app.app_context():
            u = _get_user("senior")
            # Ensure clean state
            existing = _db.session.get(UserOnlineStatus, u.id)
            if existing:
                _db.session.delete(existing)
                _db.session.commit()

            status = UserOnlineStatusRepository.set_online(u.id, "sock-123", commit=True)
            assert status.is_online is True
            assert status.socket_id == "sock-123"

            _db.session.delete(status)
            _db.session.commit()

    def test_set_online_existing_user(self, app):
        with app.app_context():
            u = _get_user("senior")
            existing = _db.session.get(UserOnlineStatus, u.id)
            if existing:
                _db.session.delete(existing)
                _db.session.commit()

            UserOnlineStatusRepository.set_online(u.id, "sock-1", commit=True)
            status = UserOnlineStatusRepository.set_online(u.id, "sock-2", commit=True)
            assert status.socket_id == "sock-2"

            _db.session.delete(status)
            _db.session.commit()

    def test_set_offline(self, app):
        with app.app_context():
            u = _get_user("senior")
            existing = _db.session.get(UserOnlineStatus, u.id)
            if existing:
                _db.session.delete(existing)
                _db.session.commit()

            UserOnlineStatusRepository.set_online(u.id, "sock-1", commit=True)
            status = UserOnlineStatusRepository.set_offline(u.id, commit=True)
            assert status is not None
            assert status.is_online is False

            _db.session.delete(status)
            _db.session.commit()

    def test_set_offline_nonexistent(self, app):
        with app.app_context():
            result = UserOnlineStatusRepository.set_offline(999999, commit=True)
            assert result is None

    def test_get_by_user_id(self, app):
        with app.app_context():
            u = _get_user("senior")
            existing = _db.session.get(UserOnlineStatus, u.id)
            if existing:
                _db.session.delete(existing)
                _db.session.commit()

            UserOnlineStatusRepository.set_online(u.id, "sock-abc", commit=True)
            fetched = UserOnlineStatusRepository.get_by_user_id(u.id)
            assert fetched is not None
            assert fetched.socket_id == "sock-abc"

            _db.session.delete(fetched)
            _db.session.commit()

    def test_get_online_users(self, app):
        with app.app_context():
            u = _get_user("senior")
            existing = _db.session.get(UserOnlineStatus, u.id)
            if existing:
                _db.session.delete(existing)
                _db.session.commit()

            UserOnlineStatusRepository.set_online(u.id, "sock-x", commit=True)
            online = UserOnlineStatusRepository.get_online_users()
            assert any(s.user_id == u.id for s in online)

            status = _db.session.get(UserOnlineStatus, u.id)
            _db.session.delete(status)
            _db.session.commit()


# =========================================================================
# EquipmentRepository
# =========================================================================

class TestEquipmentRepository:

    def _make_equipment(self, **kwargs):
        defaults = dict(name=_unique("EQ"), category="analyzer", status="normal")
        defaults.update(kwargs)
        eq = Equipment(**defaults)
        _db.session.add(eq)
        _db.session.commit()
        return eq

    def test_get_by_id(self, app):
        with app.app_context():
            eq = self._make_equipment()
            assert EquipmentRepository.get_by_id(eq.id) is not None
            assert EquipmentRepository.get_by_id(999999) is None
            _db.session.delete(eq)
            _db.session.commit()

    def test_get_all_active(self, app):
        with app.app_context():
            eq1 = self._make_equipment(status="normal")
            eq2 = self._make_equipment(status="retired")
            eq3 = self._make_equipment(status=None)

            results = EquipmentRepository.get_all_active()
            ids = [r.id for r in results]
            assert eq1.id in ids
            assert eq2.id not in ids
            assert eq3.id in ids

            for e in [eq1, eq2, eq3]:
                _db.session.delete(e)
            _db.session.commit()

    def test_get_by_category(self, app):
        with app.app_context():
            cat = _unique("cat")
            eq = self._make_equipment(category=cat)
            eq_retired = self._make_equipment(category=cat, status="retired")

            results = EquipmentRepository.get_by_category(cat)
            ids = [r.id for r in results]
            assert eq.id in ids
            assert eq_retired.id not in ids

            _db.session.delete(eq)
            _db.session.delete(eq_retired)
            _db.session.commit()

    def test_get_by_categories(self, app):
        with app.app_context():
            cat1, cat2 = _unique("c1"), _unique("c2")
            eq1 = self._make_equipment(category=cat1)
            eq2 = self._make_equipment(category=cat2)

            results = EquipmentRepository.get_by_categories([cat1, cat2])
            ids = [r.id for r in results]
            assert eq1.id in ids
            assert eq2.id in ids

            _db.session.delete(eq1)
            _db.session.delete(eq2)
            _db.session.commit()

    def test_get_calibration_due(self, app):
        with app.app_context():
            today = date.today()
            eq = self._make_equipment(
                next_calibration_date=today + timedelta(days=5),
                status="normal",
            )
            results = EquipmentRepository.get_calibration_due(today, today + timedelta(days=10))
            ids = [r.id for r in results]
            assert eq.id in ids

            _db.session.delete(eq)
            _db.session.commit()

    def test_get_calibration_due_with_categories(self, app):
        with app.app_context():
            today = date.today()
            cat = _unique("cal")
            eq = self._make_equipment(
                next_calibration_date=today + timedelta(days=3),
                status="normal",
                category=cat,
            )
            results = EquipmentRepository.get_calibration_due(today, today + timedelta(days=10), categories=[cat])
            assert any(r.id == eq.id for r in results)

            results_other = EquipmentRepository.get_calibration_due(today, today + timedelta(days=10), categories=["nonexistent"])
            assert not any(r.id == eq.id for r in results_other)

            _db.session.delete(eq)
            _db.session.commit()

    def test_get_calibration_overdue(self, app):
        with app.app_context():
            today = date.today()
            eq = self._make_equipment(
                next_calibration_date=today - timedelta(days=5),
                status="normal",
            )
            results = EquipmentRepository.get_calibration_overdue(today)
            ids = [r.id for r in results]
            assert eq.id in ids

            _db.session.delete(eq)
            _db.session.commit()

    def test_get_calibration_overdue_with_categories(self, app):
        with app.app_context():
            today = date.today()
            cat = _unique("ovc")
            eq = self._make_equipment(
                next_calibration_date=today - timedelta(days=5),
                status="normal",
                category=cat,
            )
            results = EquipmentRepository.get_calibration_overdue(today, categories=[cat])
            assert any(r.id == eq.id for r in results)

            _db.session.delete(eq)
            _db.session.commit()

    def test_get_by_statuses(self, app):
        with app.app_context():
            eq = self._make_equipment(status="maintenance")
            results = EquipmentRepository.get_by_statuses(["maintenance"])
            assert any(r.id == eq.id for r in results)

            _db.session.delete(eq)
            _db.session.commit()

    def test_get_by_statuses_with_categories(self, app):
        with app.app_context():
            cat = _unique("sc")
            eq = self._make_equipment(status="maintenance", category=cat)
            results = EquipmentRepository.get_by_statuses(["maintenance"], categories=[cat])
            assert any(r.id == eq.id for r in results)

            results_other = EquipmentRepository.get_by_statuses(["maintenance"], categories=["nope"])
            assert not any(r.id == eq.id for r in results_other)

            _db.session.delete(eq)
            _db.session.commit()

    def test_get_by_related_analysis_no_category(self, app):
        with app.app_context():
            eq = self._make_equipment(related_analysis="Mad,Aad,Vdaf")
            results = EquipmentRepository.get_by_related_analysis("%Mad%")
            assert any(r.id == eq.id for r in results)

            _db.session.delete(eq)
            _db.session.commit()

    def test_get_by_related_analysis_with_category(self, app):
        with app.app_context():
            cat = _unique("ra")
            eq = self._make_equipment(related_analysis="St,d", category=cat)
            results = EquipmentRepository.get_by_related_analysis("%St%", category=cat)
            assert any(r.id == eq.id for r in results)

            _db.session.delete(eq)
            _db.session.commit()

    def test_save_and_delete(self, app):
        with app.app_context():
            eq = Equipment(name="ToDelete", category="other", status="normal")
            saved = EquipmentRepository.save(eq, commit=True)
            assert saved.id is not None

            result = EquipmentRepository.delete(saved, commit=True)
            assert result is True


# =========================================================================
# AuditLogRepository
# =========================================================================

class TestAuditLogRepository:

    def _make_audit(self, **kwargs):
        defaults = dict(action="test_action", resource_type="Sample", resource_id=1)
        defaults.update(kwargs)
        log = AuditLog(**defaults)
        _db.session.add(log)
        _db.session.commit()
        return log

    def test_save_and_get_by_id(self, app):
        with app.app_context():
            log = AuditLog(action="login", user_id=_get_user().id)
            saved = AuditLogRepository.save(log, commit=True)
            assert saved.id is not None

            fetched = AuditLogRepository.get_by_id(saved.id)
            assert fetched is not None
            assert fetched.action == "login"

    def test_get_by_id_none(self, app):
        with app.app_context():
            assert AuditLogRepository.get_by_id(999999) is None

    def test_get_recent(self, app):
        with app.app_context():
            u = _get_user()
            log = AuditLog(action="recent_test", user_id=u.id)
            _db.session.add(log)
            _db.session.commit()

            results = AuditLogRepository.get_recent(limit=200)
            assert any(r.action == "recent_test" for r in results)

    def test_get_by_user(self, app):
        with app.app_context():
            u = _get_user()
            log = AuditLog(action="user_action", user_id=u.id)
            _db.session.add(log)
            _db.session.commit()

            results = AuditLogRepository.get_by_user(u.id)
            assert any(r.action == "user_action" for r in results)

    def test_get_by_action(self, app):
        with app.app_context():
            unique_action = _unique("act")
            log = AuditLog(action=unique_action)
            _db.session.add(log)
            _db.session.commit()

            results = AuditLogRepository.get_by_action(unique_action)
            assert len(results) >= 1

    def test_get_by_resource(self, app):
        with app.app_context():
            log = AuditLog(action="res_test", resource_type="Equipment", resource_id=42)
            _db.session.add(log)
            _db.session.commit()

            results = AuditLogRepository.get_by_resource("Equipment", 42)
            assert any(r.action == "res_test" for r in results)

    def test_get_by_date_range_no_filters(self, app):
        with app.app_context():
            results = AuditLogRepository.get_by_date_range()
            assert isinstance(results, list)

    def test_get_by_date_range_all_filters(self, app):
        with app.app_context():
            u = _get_user()
            now = datetime.utcnow()
            unique_action = _unique("dr")
            log = AuditLog(action=unique_action, user_id=u.id, timestamp=now)
            _db.session.add(log)
            _db.session.commit()

            results = AuditLogRepository.get_by_date_range(
                start_date=now - timedelta(seconds=10),
                end_date=now + timedelta(seconds=10),
                action=unique_action,
                user_id=u.id,
            )
            assert len(results) >= 1

    def test_get_by_date_range_start_only(self, app):
        with app.app_context():
            results = AuditLogRepository.get_by_date_range(
                start_date=datetime.utcnow() - timedelta(days=1)
            )
            assert isinstance(results, list)

    def test_get_by_date_range_end_only(self, app):
        with app.app_context():
            results = AuditLogRepository.get_by_date_range(
                end_date=datetime.utcnow() + timedelta(days=1)
            )
            assert isinstance(results, list)


# =========================================================================
# LabReportRepository & ReportSignatureRepository
# =========================================================================

class TestLabReportRepository:

    def _make_report(self, **kwargs):
        defaults = dict(
            report_number=_unique("RPT"),
            lab_type="coal",
            status="draft",
        )
        defaults.update(kwargs)
        rpt = LabReport(**defaults)
        _db.session.add(rpt)
        _db.session.commit()
        return rpt

    def test_save_and_get_by_id(self, app):
        with app.app_context():
            rpt = self._make_report()
            fetched = LabReportRepository.get_by_id(rpt.id)
            assert fetched is not None
            _db.session.delete(rpt)
            _db.session.commit()

    def test_get_by_id_none(self, app):
        with app.app_context():
            assert LabReportRepository.get_by_id(999999) is None

    def test_get_by_id_or_404(self, app):
        with app.app_context():
            rpt = self._make_report()
            fetched = LabReportRepository.get_by_id_or_404(rpt.id)
            assert fetched.id == rpt.id
            _db.session.delete(rpt)
            _db.session.commit()

    def test_get_by_id_or_404_raises(self, app):
        with app.app_context():
            from werkzeug.exceptions import NotFound
            with pytest.raises(NotFound):
                LabReportRepository.get_by_id_or_404(999999)

    def test_get_by_number(self, app):
        with app.app_context():
            num = _unique("NUM")
            rpt = self._make_report(report_number=num)
            fetched = LabReportRepository.get_by_number(num)
            assert fetched is not None
            assert fetched.id == rpt.id
            _db.session.delete(rpt)
            _db.session.commit()

    def test_get_by_number_not_found(self, app):
        with app.app_context():
            assert LabReportRepository.get_by_number("nonexistent") is None

    def test_get_by_lab(self, app):
        with app.app_context():
            rpt = self._make_report(lab_type="water", status="approved")
            results = LabReportRepository.get_by_lab("water")
            assert any(r.id == rpt.id for r in results)

            results_filtered = LabReportRepository.get_by_lab("water", status="approved")
            assert any(r.id == rpt.id for r in results_filtered)

            results_no_match = LabReportRepository.get_by_lab("water", status="draft")
            assert not any(r.id == rpt.id for r in results_no_match)

            _db.session.delete(rpt)
            _db.session.commit()

    def test_get_all(self, app):
        with app.app_context():
            rpt = self._make_report(status="draft")
            results = LabReportRepository.get_all()
            assert any(r.id == rpt.id for r in results)

            results_filtered = LabReportRepository.get_all(status="draft")
            assert any(r.id == rpt.id for r in results_filtered)

            _db.session.delete(rpt)
            _db.session.commit()

    def test_delete(self, app):
        with app.app_context():
            rpt = self._make_report()
            rid = rpt.id
            result = LabReportRepository.delete(rpt, commit=True)
            assert result is True
            assert LabReportRepository.get_by_id(rid) is None


class TestReportSignatureRepository:

    def _make_sig(self, **kwargs):
        defaults = dict(name="Test Sig", signature_type="signature", is_active=True, lab_type="all")
        defaults.update(kwargs)
        sig = ReportSignature(**defaults)
        _db.session.add(sig)
        _db.session.commit()
        return sig

    def test_save_and_get_by_id(self, app):
        with app.app_context():
            sig = self._make_sig()
            fetched = ReportSignatureRepository.get_by_id(sig.id)
            assert fetched is not None
            _db.session.delete(sig)
            _db.session.commit()

    def test_get_by_id_none(self, app):
        with app.app_context():
            assert ReportSignatureRepository.get_by_id(999999) is None

    def test_get_active_no_filter(self, app):
        with app.app_context():
            sig = self._make_sig(is_active=True)
            results = ReportSignatureRepository.get_active()
            assert any(r.id == sig.id for r in results)
            _db.session.delete(sig)
            _db.session.commit()

    def test_get_active_by_type(self, app):
        with app.app_context():
            sig = self._make_sig(signature_type="stamp")
            results = ReportSignatureRepository.get_active(sig_type="stamp")
            assert any(r.id == sig.id for r in results)
            _db.session.delete(sig)
            _db.session.commit()

    def test_get_active_by_lab_type(self, app):
        with app.app_context():
            sig = self._make_sig(lab_type="coal")
            results = ReportSignatureRepository.get_active(lab_type="coal")
            assert any(r.id == sig.id for r in results)

            # 'all' lab_type should also match
            sig_all = self._make_sig(lab_type="all")
            results2 = ReportSignatureRepository.get_active(lab_type="coal")
            assert any(r.id == sig_all.id for r in results2)

            _db.session.delete(sig)
            _db.session.delete(sig_all)
            _db.session.commit()

    def test_get_by_user(self, app):
        with app.app_context():
            u = _get_user()
            sig = self._make_sig(user_id=u.id)
            results = ReportSignatureRepository.get_by_user(u.id)
            assert any(r.id == sig.id for r in results)
            _db.session.delete(sig)
            _db.session.commit()

    def test_delete(self, app):
        with app.app_context():
            sig = self._make_sig()
            sid = sig.id
            ReportSignatureRepository.delete(sig, commit=True)
            assert ReportSignatureRepository.get_by_id(sid) is None


# =========================================================================
# MaintenanceLogRepository & UsageLogRepository
# =========================================================================

class TestMaintenanceLogRepository:

    def _make_equipment(self):
        eq = Equipment(name=_unique("MEQ"), category="other", status="normal")
        _db.session.add(eq)
        _db.session.commit()
        return eq

    def test_save_and_get_by_id(self, app):
        with app.app_context():
            eq = self._make_equipment()
            log = MaintenanceLog(equipment_id=eq.id, action_type="Calibration", description="test")
            saved = MaintenanceLogRepository.save(log, commit=True)
            assert saved.id is not None

            fetched = MaintenanceLogRepository.get_by_id(saved.id)
            assert fetched is not None

            # NOTE: MaintenanceLog нь ISO 17025-аар append-only тул explicit
            # cleanup-аар устгахгүй. In-memory SQLite session tear-down автомат.

    def test_get_by_id_none(self, app):
        with app.app_context():
            assert MaintenanceLogRepository.get_by_id(999999) is None

    def test_has_records(self, app):
        with app.app_context():
            eq = self._make_equipment()
            assert MaintenanceLogRepository.has_records(eq.id) is False

            log = MaintenanceLog(equipment_id=eq.id, action_type="Repair")
            _db.session.add(log)
            _db.session.commit()

            assert MaintenanceLogRepository.has_records(eq.id) is True
            # Cleanup-гүй: append-only audit record

    def test_delete_blocked(self, app):
        """MaintenanceLog нь ISO 17025-аар append-only — DELETE хориглогдсон."""
        import pytest
        with app.app_context():
            eq = self._make_equipment()
            log = MaintenanceLog(equipment_id=eq.id, action_type="Test")
            _db.session.add(log)
            _db.session.commit()

            with pytest.raises(RuntimeError, match="AUDIT INTEGRITY"):
                MaintenanceLogRepository.delete(log, commit=True)
            _db.session.rollback()


class TestUsageLogRepository:

    def _make_equipment(self):
        eq = Equipment(name=_unique("UEQ"), category="other", status="normal")
        _db.session.add(eq)
        _db.session.commit()
        return eq

    def test_save_and_get_by_id(self, app):
        with app.app_context():
            eq = self._make_equipment()
            log = UsageLog(equipment_id=eq.id, start_time=datetime.utcnow())
            saved = UsageLogRepository.save(log, commit=True)
            assert saved.id is not None

            fetched = UsageLogRepository.get_by_id(saved.id)
            assert fetched is not None
            # UsageLog нь ISO 17025-аар append-only тул explicit delete cleanup-гүй

    def test_get_by_id_none(self, app):
        with app.app_context():
            assert UsageLogRepository.get_by_id(999999) is None

    def test_get_by_equipment(self, app):
        with app.app_context():
            eq = self._make_equipment()
            log = UsageLog(equipment_id=eq.id, start_time=datetime.utcnow())
            _db.session.add(log)
            _db.session.commit()

            results = UsageLogRepository.get_by_equipment(eq.id)
            assert len(results) >= 1
            # Append-only — cleanup-гүй

    def test_has_records(self, app):
        with app.app_context():
            eq = self._make_equipment()
            assert UsageLogRepository.has_records(eq.id) is False

            log = UsageLog(equipment_id=eq.id, start_time=datetime.utcnow())
            _db.session.add(log)
            _db.session.commit()

            assert UsageLogRepository.has_records(eq.id) is True
            # Append-only — cleanup-гүй


# =========================================================================
# AnalysisResultRepository
# =========================================================================

class TestAnalysisResultRepository:

    def _make_sample(self):
        u = _get_user()
        s = Sample(sample_code=_unique("SMP"), user_id=u.id, client_name="QC", sample_type="coal")
        _db.session.add(s)
        _db.session.commit()
        return s

    def _make_result(self, sample_id, **kwargs):
        defaults = dict(
            sample_id=sample_id,
            analysis_code="Mad",
            status="pending_review",
        )
        defaults.update(kwargs)
        ar = AnalysisResult(**defaults)
        _db.session.add(ar)
        _db.session.commit()
        return ar

    def test_get_by_id(self, app):
        with app.app_context():
            s = self._make_sample()
            ar = self._make_result(s.id)
            assert AnalysisResultRepository.get_by_id(ar.id) is not None
            assert AnalysisResultRepository.get_by_id(999999) is None
            _db.session.delete(ar)
            _db.session.delete(s)
            _db.session.commit()

    def test_get_by_id_or_404(self, app):
        with app.app_context():
            s = self._make_sample()
            ar = self._make_result(s.id)
            fetched = AnalysisResultRepository.get_by_id_or_404(ar.id)
            assert fetched.id == ar.id

            from werkzeug.exceptions import NotFound
            with pytest.raises(NotFound):
                AnalysisResultRepository.get_by_id_or_404(999999)

            _db.session.delete(ar)
            _db.session.delete(s)
            _db.session.commit()

    def test_get_by_ids(self, app):
        with app.app_context():
            s = self._make_sample()
            ar1 = self._make_result(s.id, analysis_code="Mad")
            ar2 = self._make_result(s.id, analysis_code="Aad")

            results = AnalysisResultRepository.get_by_ids([ar1.id, ar2.id])
            assert len(results) == 2

            # empty list
            assert AnalysisResultRepository.get_by_ids([]) == []

            _db.session.delete(ar1)
            _db.session.delete(ar2)
            _db.session.delete(s)
            _db.session.commit()

    def test_get_by_sample_id(self, app):
        with app.app_context():
            s = self._make_sample()
            ar = self._make_result(s.id)
            results = AnalysisResultRepository.get_by_sample_id(s.id)
            assert any(r.id == ar.id for r in results)

            _db.session.delete(ar)
            _db.session.delete(s)
            _db.session.commit()

    def test_get_by_sample_ids(self, app):
        with app.app_context():
            s1 = self._make_sample()
            s2 = self._make_sample()
            ar1 = self._make_result(s1.id)
            ar2 = self._make_result(s2.id)

            results = AnalysisResultRepository.get_by_sample_ids([s1.id, s2.id])
            ids = [r.id for r in results]
            assert ar1.id in ids
            assert ar2.id in ids

            assert AnalysisResultRepository.get_by_sample_ids([]) == []

            _db.session.delete(ar1)
            _db.session.delete(ar2)
            _db.session.delete(s1)
            _db.session.delete(s2)
            _db.session.commit()

    def test_get_approved_by_sample(self, app):
        with app.app_context():
            s = self._make_sample()
            ar_approved = self._make_result(s.id, status="approved", analysis_code="Aad")
            ar_pending = self._make_result(s.id, status="rejected", analysis_code="Vdaf")

            results = AnalysisResultRepository.get_approved_by_sample(s.id)
            ids = [r.id for r in results]
            assert ar_approved.id in ids
            assert ar_pending.id not in ids

            _db.session.delete(ar_approved)
            _db.session.delete(ar_pending)
            _db.session.delete(s)
            _db.session.commit()

    def test_get_approved_by_sample_ids(self, app):
        with app.app_context():
            s = self._make_sample()
            ar = self._make_result(s.id, status="approved")

            results = AnalysisResultRepository.get_approved_by_sample_ids([s.id])
            assert any(r.id == ar.id for r in results)

            assert AnalysisResultRepository.get_approved_by_sample_ids([]) == []

            _db.session.delete(ar)
            _db.session.delete(s)
            _db.session.commit()

    def test_get_by_status(self, app):
        with app.app_context():
            s = self._make_sample()
            ar = self._make_result(s.id, status="pending_review")

            results = AnalysisResultRepository.get_by_status("pending_review")
            assert any(r.id == ar.id for r in results)

            _db.session.delete(ar)
            _db.session.delete(s)
            _db.session.commit()

    def test_get_pending_review(self, app):
        with app.app_context():
            s = self._make_sample()
            ar = self._make_result(s.id, status="pending_review", analysis_code="FCd")

            results = AnalysisResultRepository.get_pending_review()
            assert any(r.id == ar.id for r in results)

            _db.session.delete(ar)
            _db.session.delete(s)
            _db.session.commit()

    def test_update_status(self, app):
        with app.app_context():
            s = self._make_sample()
            ar = self._make_result(s.id, status="pending_review")

            count = AnalysisResultRepository.update_status([ar.id], "approved", commit=True)
            assert count == 1

            _db.session.expire_all()
            refreshed = AnalysisResultRepository.get_by_id(ar.id)
            assert refreshed.status == "approved"

            # empty list
            assert AnalysisResultRepository.update_status([], "approved", commit=True) == 0

            _db.session.delete(refreshed)
            _db.session.delete(s)
            _db.session.commit()

    def test_get_by_analysis_code(self, app):
        with app.app_context():
            s = self._make_sample()
            code = _unique("AC")
            ar = self._make_result(s.id, analysis_code=code)

            results = AnalysisResultRepository.get_by_analysis_code(code)
            assert any(r.id == ar.id for r in results)

            _db.session.delete(ar)
            _db.session.delete(s)
            _db.session.commit()

    def test_get_by_sample_and_code(self, app):
        with app.app_context():
            s = self._make_sample()
            code = _unique("SC")
            ar = self._make_result(s.id, analysis_code=code)

            fetched = AnalysisResultRepository.get_by_sample_and_code(s.id, code)
            assert fetched is not None
            assert fetched.id == ar.id

            assert AnalysisResultRepository.get_by_sample_and_code(s.id, "NONEXIST") is None

            _db.session.delete(ar)
            _db.session.delete(s)
            _db.session.commit()

    def test_get_status_map_for_samples(self, app):
        with app.app_context():
            s = self._make_sample()
            ar1 = self._make_result(s.id, status="approved", analysis_code="A1")
            ar2 = self._make_result(s.id, status="rejected", analysis_code="A2")

            smap = AnalysisResultRepository.get_status_map_for_samples([s.id])
            assert s.id in smap
            assert "approved" in smap[s.id]
            assert "rejected" in smap[s.id]

            assert AnalysisResultRepository.get_status_map_for_samples([]) == {}

            _db.session.delete(ar1)
            _db.session.delete(ar2)
            _db.session.delete(s)
            _db.session.commit()

    def test_samples_with_approved_results(self, app):
        with app.app_context():
            s = self._make_sample()
            ar = self._make_result(s.id, status="approved")

            result_ids = AnalysisResultRepository.samples_with_approved_results()
            assert s.id in result_ids

            _db.session.delete(ar)
            _db.session.delete(s)
            _db.session.commit()

    def test_save_and_delete(self, app):
        with app.app_context():
            s = self._make_sample()
            ar = AnalysisResult(sample_id=s.id, analysis_code="Del", status="pending_review")
            saved = AnalysisResultRepository.save(ar, commit=True)
            assert saved.id is not None

            result = AnalysisResultRepository.delete(saved, commit=True)
            assert result is True

            _db.session.delete(s)
            _db.session.commit()

    def test_save_no_commit(self, app):
        with app.app_context():
            s = self._make_sample()
            ar = AnalysisResult(sample_id=s.id, analysis_code="NC", status="pending_review")
            AnalysisResultRepository.save(ar, commit=False)
            _db.session.commit()
            assert ar.id is not None

            _db.session.delete(ar)
            _db.session.delete(s)
            _db.session.commit()


# =========================================================================
# SystemSettingRepository
# =========================================================================

class TestSystemSettingRepository:

    def test_set_value_creates_new(self, app):
        with app.app_context():
            cat, key = _unique("cat"), _unique("key")
            setting = SystemSettingRepository.set_value(cat, key, "hello", commit=True)
            assert setting.id is not None
            assert setting.value == "hello"

            _db.session.delete(setting)
            _db.session.commit()

    def test_set_value_updates_existing(self, app):
        with app.app_context():
            cat, key = _unique("cat"), _unique("key")
            SystemSettingRepository.set_value(cat, key, "first", commit=True)
            setting = SystemSettingRepository.set_value(cat, key, "second", commit=True)
            assert setting.value == "second"

            _db.session.delete(setting)
            _db.session.commit()

    def test_get(self, app):
        with app.app_context():
            cat, key = _unique("cat"), _unique("key")
            SystemSettingRepository.set_value(cat, key, "val", commit=True)

            fetched = SystemSettingRepository.get(cat, key)
            assert fetched is not None
            assert fetched.value == "val"

            assert SystemSettingRepository.get("nonexistent", "nope") is None

            _db.session.delete(fetched)
            _db.session.commit()

    def test_get_value(self, app):
        with app.app_context():
            cat, key = _unique("cat"), _unique("key")
            SystemSettingRepository.set_value(cat, key, "myval", commit=True)

            val = SystemSettingRepository.get_value(cat, key)
            assert val == "myval"

            default = SystemSettingRepository.get_value("no", "no", default="fallback")
            assert default == "fallback"

            s = SystemSettingRepository.get(cat, key)
            _db.session.delete(s)
            _db.session.commit()

    def test_get_json(self, app):
        with app.app_context():
            cat, key = _unique("cat"), _unique("key")
            SystemSettingRepository.set_value(cat, key, '{"a": 1}', commit=True)

            val = SystemSettingRepository.get_json(cat, key)
            assert val == {"a": 1}

            # invalid json
            cat2, key2 = _unique("cat"), _unique("key")
            SystemSettingRepository.set_value(cat2, key2, "not json{{{", commit=True)
            val2 = SystemSettingRepository.get_json(cat2, key2, default="def")
            assert val2 == "def"

            # nonexistent
            val3 = SystemSettingRepository.get_json("no", "no", default=42)
            assert val3 == 42

            for c, k in [(cat, key), (cat2, key2)]:
                s = SystemSettingRepository.get(c, k)
                if s:
                    _db.session.delete(s)
            _db.session.commit()

    def test_get_all_by_category(self, app):
        with app.app_context():
            cat = _unique("cat")
            SystemSettingRepository.set_value(cat, "k1", "v1", commit=True)
            SystemSettingRepository.set_value(cat, "k2", "v2", commit=True)

            results = SystemSettingRepository.get_all_by_category(cat)
            assert len(results) == 2

            for r in results:
                _db.session.delete(r)
            _db.session.commit()

    def test_get_email_recipients(self, app):
        with app.app_context():
            # No settings exist initially for email
            to_val, cc_val = SystemSettingRepository.get_email_recipients()
            # They may be empty strings or actual values
            assert isinstance(to_val, str)
            assert isinstance(cc_val, str)

    def test_get_email_recipients_with_data(self, app):
        with app.app_context():
            SystemSettingRepository.set_value("email", "report_recipients_to", "a@b.com", commit=True)
            SystemSettingRepository.set_value("email", "report_recipients_cc", "c@d.com", commit=True)

            to_val, cc_val = SystemSettingRepository.get_email_recipients()
            assert to_val == "a@b.com"
            assert cc_val == "c@d.com"

            for k in ["report_recipients_to", "report_recipients_cc"]:
                s = SystemSettingRepository.get("email", k)
                if s:
                    _db.session.delete(s)
            _db.session.commit()

    def test_get_gi_shift_config(self, app):
        with app.app_context():
            # May return None if not set
            result = SystemSettingRepository.get_gi_shift_config()
            # just verify it doesn't crash
            assert result is None or isinstance(result, SystemSetting)

    def test_get_repeatability_limits(self, app):
        with app.app_context():
            result = SystemSettingRepository.get_repeatability_limits()
            assert result is None or isinstance(result, SystemSetting)

    def test_delete(self, app):
        with app.app_context():
            cat, key = _unique("cat"), _unique("key")
            setting = SystemSettingRepository.set_value(cat, key, "to_delete", commit=True)
            sid = setting.id
            SystemSettingRepository.delete(setting, commit=True)
            assert SystemSettingRepository.get(cat, key) is None


# =========================================================================
# ChemicalRepository
# =========================================================================

class TestChemicalRepository:

    def _make_chemical(self, **kwargs):
        defaults = dict(name=_unique("CHEM"), status="active", quantity=100, unit="mL")
        defaults.update(kwargs)
        c = Chemical(**defaults)
        _db.session.add(c)
        _db.session.commit()
        return c

    def test_get_by_id(self, app):
        with app.app_context():
            c = self._make_chemical()
            assert ChemicalRepository.get_by_id(c.id) is not None
            assert ChemicalRepository.get_by_id(999999) is None
            _db.session.delete(c)
            _db.session.commit()

    def test_get_active_count(self, app):
        with app.app_context():
            c = self._make_chemical(status="active")
            count = ChemicalRepository.get_active_count()
            assert count >= 1
            _db.session.delete(c)
            _db.session.commit()

    def test_get_low_stock_count(self, app):
        with app.app_context():
            c = self._make_chemical(status="low_stock")
            count = ChemicalRepository.get_low_stock_count()
            assert count >= 1
            _db.session.delete(c)
            _db.session.commit()

    def test_get_expired_count(self, app):
        with app.app_context():
            c = self._make_chemical(status="expired")
            count = ChemicalRepository.get_expired_count()
            assert count >= 1
            _db.session.delete(c)
            _db.session.commit()

    def test_get_low_stock(self, app):
        with app.app_context():
            c = self._make_chemical(status="low_stock")
            results = ChemicalRepository.get_low_stock()
            assert any(r.id == c.id for r in results)
            _db.session.delete(c)
            _db.session.commit()

    def test_get_expiring_before(self, app):
        with app.app_context():
            tomorrow = date.today() + timedelta(days=1)
            c = self._make_chemical(expiry_date=date.today(), status="active")
            results = ChemicalRepository.get_expiring_before(tomorrow)
            assert any(r.id == c.id for r in results)
            _db.session.delete(c)
            _db.session.commit()

    def test_get_expiring_before_excludes_disposed(self, app):
        with app.app_context():
            tomorrow = date.today() + timedelta(days=1)
            c = self._make_chemical(expiry_date=date.today(), status="disposed")
            results = ChemicalRepository.get_expiring_before(tomorrow)
            assert not any(r.id == c.id for r in results)
            _db.session.delete(c)
            _db.session.commit()

    def test_get_active_no_filter(self, app):
        with app.app_context():
            c = self._make_chemical(status="active")
            results = ChemicalRepository.get_active()
            assert any(r.id == c.id for r in results)
            _db.session.delete(c)
            _db.session.commit()

    def test_get_active_by_lab_type(self, app):
        with app.app_context():
            c = self._make_chemical(status="active", lab_type="water")
            results = ChemicalRepository.get_active(lab_type="water")
            assert any(r.id == c.id for r in results)

            # 'all' lab_type should also appear
            c_all = self._make_chemical(status="active", lab_type="all")
            results2 = ChemicalRepository.get_active(lab_type="water")
            assert any(r.id == c_all.id for r in results2)

            _db.session.delete(c)
            _db.session.delete(c_all)
            _db.session.commit()

    def test_get_for_water_lab(self, app):
        with app.app_context():
            c_water = self._make_chemical(status="active", lab_type="water")
            c_all = self._make_chemical(status="active", lab_type="all")
            c_coal = self._make_chemical(status="active", lab_type="coal")

            results = ChemicalRepository.get_for_water_lab()
            ids = [r.id for r in results]
            assert c_water.id in ids
            assert c_all.id in ids
            assert c_coal.id not in ids

            _db.session.delete(c_water)
            _db.session.delete(c_all)
            _db.session.delete(c_coal)
            _db.session.commit()

    def test_save_and_delete(self, app):
        with app.app_context():
            c = Chemical(name="ToDelete", status="active", quantity=1, unit="g")
            saved = ChemicalRepository.save(c, commit=True)
            assert saved.id is not None

            result = ChemicalRepository.delete(saved, commit=True)
            assert result is True


# =========================================================================
# UserRepository
# =========================================================================

class TestUserRepository:

    def test_get_by_id(self, app):
        with app.app_context():
            u = _get_user()
            fetched = UserRepository.get_by_id(u.id)
            assert fetched is not None
            assert fetched.username == "chemist"

    def test_get_by_id_none(self, app):
        with app.app_context():
            assert UserRepository.get_by_id(999999) is None

    def test_get_by_id_or_404(self, app):
        with app.app_context():
            u = _get_user()
            fetched = UserRepository.get_by_id_or_404(u.id)
            assert fetched.id == u.id

    def test_get_by_id_or_404_raises(self, app):
        with app.app_context():
            from werkzeug.exceptions import NotFound
            with pytest.raises(NotFound):
                UserRepository.get_by_id_or_404(999999)

    def test_get_by_username(self, app):
        with app.app_context():
            fetched = UserRepository.get_by_username("admin")
            assert fetched is not None
            assert fetched.username == "admin"

            assert UserRepository.get_by_username("nonexistent") is None

    def test_username_exists(self, app):
        with app.app_context():
            assert UserRepository.username_exists("admin") is True
            assert UserRepository.username_exists("nonexistent") is False

    def test_username_exists_exclude_id(self, app):
        with app.app_context():
            u = UserRepository.get_by_username("admin")
            # Exclude the admin's own id - should return False
            assert UserRepository.username_exists("admin", exclude_id=u.id) is False
            # Exclude a different id - should return True
            assert UserRepository.username_exists("admin", exclude_id=999999) is True

    def test_get_all(self, app):
        with app.app_context():
            users = UserRepository.get_all()
            assert len(users) >= 3  # admin, chemist, senior
            usernames = [u.username for u in users]
            assert "admin" in usernames

    def test_get_by_role(self, app):
        with app.app_context():
            admins = UserRepository.get_by_role("admin")
            assert len(admins) >= 1
            assert all(u.role == "admin" for u in admins)

    def test_get_by_roles(self, app):
        with app.app_context():
            users = UserRepository.get_by_roles(["admin", "chemist"])
            assert len(users) >= 2
            assert all(u.role in ("admin", "chemist") for u in users)

    def test_save_and_delete(self, app):
        with app.app_context():
            u = User(username=_unique("usr"), role="chemist")
            u.set_password("TestPass123")
            saved = UserRepository.save(u, commit=True)
            assert saved.id is not None

            result = UserRepository.delete(saved, commit=True)
            assert result is True

    def test_save_no_commit(self, app):
        with app.app_context():
            u = User(username=_unique("nc"), role="chemist")
            u.set_password("TestPass123")
            UserRepository.save(u, commit=False)
            _db.session.commit()
            assert u.id is not None
            _db.session.delete(u)
            _db.session.commit()
