# tests/test_tasks_coverage.py
# -*- coding: utf-8 -*-
"""
Tests for Celery background task modules (0% coverage targets):
  - app.tasks.email_tasks
  - app.tasks.import_tasks
  - app.tasks.instrument_tasks
  - app.tasks.report_tasks
  - app.tasks.sla_tasks

Strategy:
  For bind=True tasks, we call task.run() which auto-binds 'self' to the
  task instance. We then patch task.retry to control retry behavior.
  For unbound tasks, we call the __wrapped__ original function directly.
  Lazy imports inside task bodies are patched at the source module level
  with create=True when the function may not exist yet.
"""

import os
import base64
import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock


# ===========================================================================
# email_tasks.send_email_async  (bind=True, max_retries=3)
# ===========================================================================

class TestSendEmailAsync:

    def test_success_basic(self, app):
        with app.app_context():
            from app.tasks.email_tasks import send_email_async

            with patch("app.mail") as mock_mail:
                result = send_email_async.run(
                    subject="Test Subject",
                    recipients=["a@b.com", "c@d.com"],
                    html_body="<p>Hello</p>",
                )

        assert result["success"] is True
        assert result["recipients"] == 2
        mock_mail.send.assert_called_once()

    def test_reply_to_set(self, app):
        with app.app_context():
            from app.tasks.email_tasks import send_email_async

            with patch("app.mail") as mock_mail:
                result = send_email_async.run(
                    subject="Re",
                    recipients=["x@y.com"],
                    html_body="<p>Reply</p>",
                    reply_to="z@y.com",
                )

        assert result["success"] is True
        msg = mock_mail.send.call_args[0][0]
        assert msg.reply_to == "z@y.com"

    def test_attachment_base64_string(self, app):
        with app.app_context():
            from app.tasks.email_tasks import send_email_async

            att = {
                "filename": "report.pdf",
                "content_type": "application/pdf",
                "data": base64.b64encode(b"PDF_CONTENT").decode(),
            }
            with patch("app.mail"):
                result = send_email_async.run(
                    subject="Att", recipients=["a@b.com"],
                    html_body="<p>x</p>", attachments=[att],
                )

        assert result["success"] is True

    def test_attachment_raw_bytes(self, app):
        with app.app_context():
            from app.tasks.email_tasks import send_email_async

            att = {"filename": "data.bin", "data": b"RAW_BYTES"}
            with patch("app.mail"):
                result = send_email_async.run(
                    subject="Bin", recipients=["a@b.com"],
                    html_body="<p>x</p>", attachments=[att],
                )

        assert result["success"] is True

    def test_retry_on_os_error(self, app):
        with app.app_context():
            from app.tasks.email_tasks import send_email_async

            with patch("app.mail") as mock_mail:
                mock_mail.send.side_effect = OSError("SMTP down")
                with patch.object(send_email_async, "retry", side_effect=OSError("retrying")) as mock_retry:
                    with pytest.raises(OSError, match="retrying"):
                        send_email_async.run(
                            subject="Fail", recipients=["a@b.com"],
                            html_body="<p>x</p>",
                        )

                mock_retry.assert_called_once()

    def test_retry_on_runtime_error(self, app):
        with app.app_context():
            from app.tasks.email_tasks import send_email_async

            with patch("app.mail") as mock_mail:
                mock_mail.send.side_effect = RuntimeError("no context")
                with patch.object(send_email_async, "retry", side_effect=RuntimeError("retrying")) as mock_retry:
                    with pytest.raises(RuntimeError, match="retrying"):
                        send_email_async.run(
                            subject="Fail2", recipients=["a@b.com"],
                            html_body="<p>x</p>",
                        )

                mock_retry.assert_called_once()


# ===========================================================================
# email_tasks.send_sla_overdue_alert  (bind=True, max_retries=2)
# ===========================================================================

class TestSendSlaOverdueAlert:

    @patch("app.utils.notifications.send_notification", create=True)
    @patch("app.services.sla_service.get_overdue_samples", create=True)
    @patch("app.services.sla_service.get_sla_summary", create=True)
    def test_no_overdue(self, mock_summary, mock_overdue, mock_notif, app):
        with app.app_context():
            from app.tasks.email_tasks import send_sla_overdue_alert

            mock_summary.return_value = SimpleNamespace(overdue=0, due_soon=0)
            result = send_sla_overdue_alert.run(lab_type="coal")

        assert result["success"] is True
        assert "No overdue" in result["message"]
        mock_overdue.assert_not_called()

    @patch("app.utils.notifications.send_notification", create=True)
    @patch("app.services.sla_service.get_overdue_samples", create=True)
    @patch("app.services.sla_service.get_sla_summary", create=True)
    def test_overdue_with_managers(self, mock_summary, mock_overdue, mock_notif, app):
        with app.app_context():
            from app.tasks.email_tasks import send_sla_overdue_alert
            from app.models import User

            mock_summary.return_value = SimpleNamespace(overdue=2, due_soon=1)
            mock_overdue.return_value = [
                SimpleNamespace(
                    sample_code="S001", client_name="Client A",
                    due_date="2026-03-10", overdue_hours=12.5,
                    pending_analyses="Mad, Aad",
                ),
            ]
            mock_mgr = MagicMock()
            mock_mgr.email = "mgr@lab.com"

            with patch.object(User, "query") as mock_q:
                mock_q.filter.return_value.all.return_value = [mock_mgr]
                result = send_sla_overdue_alert.run(lab_type="coal")

        assert result["success"] is True
        assert result["overdue"] == 2
        assert result["notified"] == 1
        mock_notif.assert_called_once()

    @patch("app.utils.notifications.send_notification", create=True)
    @patch("app.services.sla_service.get_overdue_samples", create=True)
    @patch("app.services.sla_service.get_sla_summary", create=True)
    def test_no_manager_emails(self, mock_summary, mock_overdue, mock_notif, app):
        with app.app_context():
            from app.tasks.email_tasks import send_sla_overdue_alert
            from app.models import User

            mock_summary.return_value = SimpleNamespace(overdue=3, due_soon=0)
            mock_overdue.return_value = []

            with patch.object(User, "query") as mock_q:
                mock_q.filter.return_value.all.return_value = []
                result = send_sla_overdue_alert.run(lab_type="water")

        assert result["success"] is False
        assert "No manager" in result["message"]

    def test_retry_on_exception(self, app):
        with app.app_context():
            from app.tasks.email_tasks import send_sla_overdue_alert

            with patch(
                "app.services.sla_service.get_sla_summary",
                create=True,
                side_effect=RuntimeError("db gone"),
            ):
                with patch.object(
                    send_sla_overdue_alert, "retry",
                    side_effect=RuntimeError("retrying"),
                ) as mock_retry:
                    with pytest.raises(RuntimeError, match="retrying"):
                        send_sla_overdue_alert.run(lab_type="coal")

                mock_retry.assert_called_once()


# ===========================================================================
# import_tasks.import_csv_async  (bind=True, max_retries=0)
# ===========================================================================

class TestImportCsvAsync:

    def test_success(self, app):
        with app.app_context():
            from app.tasks.import_tasks import import_csv_async

            with patch(
                "app.services.import_service.process_import_file",
                create=True,
            ) as mock_fn:
                mock_fn.return_value = {"success": True, "imported": 42, "errors": []}
                result = import_csv_async.run(
                    file_path="/tmp/data.csv", lab_type="coal", user_id=1,
                )

        assert result["success"] is True
        assert result["imported"] == 42
        mock_fn.assert_called_once_with(
            file_path="/tmp/data.csv", lab_type="coal",
            user_id=1, dry_run=False, batch_size=1000,
        )

    def test_with_options(self, app):
        with app.app_context():
            from app.tasks.import_tasks import import_csv_async

            with patch(
                "app.services.import_service.process_import_file",
                create=True,
            ) as mock_fn:
                mock_fn.return_value = {"success": True, "imported": 0, "errors": []}
                import_csv_async.run(
                    file_path="/tmp/big.xlsx", lab_type="water", user_id=2,
                    options={"dry_run": True, "batch_size": 500},
                )

        mock_fn.assert_called_once_with(
            file_path="/tmp/big.xlsx", lab_type="water",
            user_id=2, dry_run=True, batch_size=500,
        )

    def test_failure_returns_error(self, app):
        with app.app_context():
            from app.tasks.import_tasks import import_csv_async

            with patch(
                "app.services.import_service.process_import_file",
                create=True,
                side_effect=ValueError("Bad CSV format"),
            ):
                result = import_csv_async.run(
                    file_path="/tmp/bad.csv", lab_type="coal", user_id=1,
                )

        assert result["success"] is False
        assert "Bad CSV format" in result["error"]

    def test_options_none_defaults(self, app):
        with app.app_context():
            from app.tasks.import_tasks import import_csv_async

            with patch(
                "app.services.import_service.process_import_file",
                create=True,
            ) as mock_fn:
                mock_fn.return_value = {"success": True, "imported": 1, "errors": []}
                import_csv_async.run(
                    file_path="/tmp/x.csv", lab_type="coal", user_id=1,
                    options=None,
                )

        mock_fn.assert_called_once_with(
            file_path="/tmp/x.csv", lab_type="coal",
            user_id=1, dry_run=False, batch_size=1000,
        )


# ===========================================================================
# instrument_tasks._move_to_processed
# ===========================================================================

class TestMoveToProcessed:

    def test_basic_move(self, tmp_path):
        from app.tasks.instrument_tasks import _move_to_processed

        src = tmp_path / "data.csv"
        src.write_text("hello")

        _move_to_processed(str(src), str(tmp_path / "_processed"), "tga")

        assert (tmp_path / "_processed" / "tga" / "data.csv").exists()
        assert not src.exists()

    def test_name_collision(self, tmp_path):
        from app.tasks.instrument_tasks import _move_to_processed

        src = tmp_path / "data.csv"
        src.write_text("new")
        dest_dir = tmp_path / "_processed" / "tga"
        dest_dir.mkdir(parents=True)
        (dest_dir / "data.csv").write_text("old")

        _move_to_processed(str(src), str(tmp_path / "_processed"), "tga")

        assert (dest_dir / "data_1.csv").exists()
        assert not src.exists()

    def test_multiple_collisions(self, tmp_path):
        from app.tasks.instrument_tasks import _move_to_processed

        src = tmp_path / "data.csv"
        src.write_text("newest")
        dest_dir = tmp_path / "_processed" / "tga"
        dest_dir.mkdir(parents=True)
        (dest_dir / "data.csv").write_text("old")
        (dest_dir / "data_1.csv").write_text("old2")

        _move_to_processed(str(src), str(tmp_path / "_processed"), "tga")

        assert (dest_dir / "data_2.csv").exists()

    def test_cross_device_fallback(self, tmp_path):
        from app.tasks.instrument_tasks import _move_to_processed

        src = tmp_path / "cross.csv"
        src.write_text("data")

        with patch("os.rename", side_effect=OSError("cross-device")):
            with patch("shutil.move") as mock_shutil:
                _move_to_processed(str(src), str(tmp_path / "_processed"), "elemental")
                mock_shutil.assert_called_once()


# ===========================================================================
# instrument_tasks.scan_instrument_dirs  (bind=True via celery_app.task)
# ===========================================================================

class TestScanInstrumentDirs:

    def _configure(self, app, tmp_path, watch_dirs, base_path=""):
        app.config["INSTRUMENT_WATCH_DIRS"] = watch_dirs
        app.config["INSTRUMENT_BASE_PATH"] = base_path
        app.config["INSTRUMENT_PROCESSED_DIR"] = str(tmp_path / "_processed")

    @patch("app.tasks.instrument_tasks._move_to_processed")
    def test_imports_valid_file(self, mock_move, app, tmp_path):
        with app.app_context():
            from app.tasks.instrument_tasks import scan_instrument_dirs

            tga_dir = tmp_path / "tga"
            tga_dir.mkdir()
            (tga_dir / "reading1.csv").write_text("data")
            self._configure(app, tmp_path, {"tga": str(tga_dir)})

            with patch(
                "app.services.instrument_service.import_instrument_file",
                create=True, return_value=5,
            ) as mock_import:
                result = scan_instrument_dirs.run()

        assert result["imported"] == 5
        mock_import.assert_called_once()
        mock_move.assert_called_once()

    @patch("app.tasks.instrument_tasks._move_to_processed")
    def test_skips_hidden_and_temp(self, mock_move, app, tmp_path):
        with app.app_context():
            from app.tasks.instrument_tasks import scan_instrument_dirs

            tga_dir = tmp_path / "tga"
            tga_dir.mkdir()
            (tga_dir / ".hidden").write_text("skip")
            (tga_dir / "~tempfile").write_text("skip")
            self._configure(app, tmp_path, {"tga": str(tga_dir)})

            with patch(
                "app.services.instrument_service.import_instrument_file",
                create=True,
            ) as mock_import:
                result = scan_instrument_dirs.run()

        assert result["imported"] == 0
        mock_import.assert_not_called()

    @patch("app.tasks.instrument_tasks._move_to_processed")
    def test_skips_subdirs(self, mock_move, app, tmp_path):
        with app.app_context():
            from app.tasks.instrument_tasks import scan_instrument_dirs

            tga_dir = tmp_path / "tga"
            tga_dir.mkdir()
            (tga_dir / "subdir").mkdir()
            self._configure(app, tmp_path, {"tga": str(tga_dir)})

            with patch(
                "app.services.instrument_service.import_instrument_file",
                create=True,
            ):
                result = scan_instrument_dirs.run()

        assert result["imported"] == 0

    def test_skips_nonexistent_dir(self, app):
        with app.app_context():
            from app.tasks.instrument_tasks import scan_instrument_dirs

            app.config["INSTRUMENT_WATCH_DIRS"] = {"tga": "/nonexistent/dir"}
            app.config["INSTRUMENT_BASE_PATH"] = ""
            app.config["INSTRUMENT_PROCESSED_DIR"] = "/tmp/_proc"

            result = scan_instrument_dirs.run()

        assert result["imported"] == 0

    @patch("app.tasks.instrument_tasks._move_to_processed")
    def test_value_error_moves_file(self, mock_move, app, tmp_path):
        with app.app_context():
            from app.tasks.instrument_tasks import scan_instrument_dirs

            tga_dir = tmp_path / "tga"
            tga_dir.mkdir()
            (tga_dir / "dup.csv").write_text("dup")
            self._configure(app, tmp_path, {"tga": str(tga_dir)})

            with patch(
                "app.services.instrument_service.import_instrument_file",
                create=True, side_effect=ValueError("Duplicate"),
            ):
                result = scan_instrument_dirs.run()

        assert result["imported"] == 0
        mock_move.assert_called_once()

    @patch("app.tasks.instrument_tasks._move_to_processed")
    def test_generic_exception_not_moved(self, mock_move, app, tmp_path):
        with app.app_context():
            from app.tasks.instrument_tasks import scan_instrument_dirs

            tga_dir = tmp_path / "tga"
            tga_dir.mkdir()
            (tga_dir / "bad.csv").write_text("bad")
            self._configure(app, tmp_path, {"tga": str(tga_dir)})

            with patch(
                "app.services.instrument_service.import_instrument_file",
                create=True, side_effect=RuntimeError("boom"),
            ):
                result = scan_instrument_dirs.run()

        assert result["imported"] == 0
        mock_move.assert_not_called()

    @patch("app.tasks.instrument_tasks._move_to_processed")
    def test_with_base_path(self, mock_move, app, tmp_path):
        with app.app_context():
            from app.tasks.instrument_tasks import scan_instrument_dirs

            data_dir = tmp_path / "tga_data"
            data_dir.mkdir()
            (data_dir / "file.csv").write_text("ok")
            self._configure(app, tmp_path, {"tga": "tga_data"}, base_path=str(tmp_path))

            with patch(
                "app.services.instrument_service.import_instrument_file",
                create=True, return_value=1,
            ):
                result = scan_instrument_dirs.run()

        assert result["imported"] == 1

    def test_default_dirs_nonexistent(self, app):
        with app.app_context():
            from app.tasks.instrument_tasks import scan_instrument_dirs

            app.config.pop("INSTRUMENT_WATCH_DIRS", None)
            app.config.pop("INSTRUMENT_BASE_PATH", None)
            app.config.pop("INSTRUMENT_PROCESSED_DIR", None)

            result = scan_instrument_dirs.run()

        assert result["imported"] == 0


# ===========================================================================
# report_tasks.generate_report_async  (bind=True, max_retries=1)
# ===========================================================================

class TestGenerateReportAsync:

    def test_monthly_report(self, app):
        with app.app_context():
            from app.tasks.report_tasks import generate_report_async

            with patch(
                "app.routes.reports.monthly_plan._generate_monthly_report",
                create=True, return_value={"file": "/tmp/monthly.pdf"},
            ):
                result = generate_report_async.run(
                    report_type="monthly", params={"year": 2026, "month": 3},
                )

        assert result["success"] is True
        assert result["data"]["file"] == "/tmp/monthly.pdf"

    def test_consumption_report(self, app):
        with app.app_context():
            from app.tasks.report_tasks import generate_report_async

            with patch(
                "app.routes.reports.consumption._generate_consumption_report",
                create=True, return_value={"file": "/tmp/consumption.pdf"},
            ):
                result = generate_report_async.run(
                    report_type="consumption", params={"lab": "coal"},
                )

        assert result["success"] is True

    def test_unknown_type(self, app):
        with app.app_context():
            from app.tasks.report_tasks import generate_report_async

            result = generate_report_async.run(
                report_type="invalid", params={},
            )

        assert result["success"] is False
        assert "Unknown report type" in result["error"]

    def test_exception_returns_error(self, app):
        with app.app_context():
            from app.tasks.report_tasks import generate_report_async

            with patch(
                "app.routes.reports.monthly_plan._generate_monthly_report",
                create=True, side_effect=RuntimeError("PDF engine failed"),
            ):
                result = generate_report_async.run(
                    report_type="monthly", params={},
                )

        assert result["success"] is False
        assert "PDF engine failed" in result["error"]


# ===========================================================================
# sla_tasks.check_sla_overdue  (unbound)
# ===========================================================================

class TestCheckSlaOverdue:

    @patch("app.tasks.email_tasks.send_sla_overdue_alert")
    @patch("app.services.sla_service.get_sla_summary", create=True)
    def test_triggers_for_overdue_labs(self, mock_summary, mock_alert, app):
        with app.app_context():
            from app.tasks.sla_tasks import check_sla_overdue

            mock_summary.side_effect = [
                SimpleNamespace(overdue=2),
                SimpleNamespace(overdue=0),
                SimpleNamespace(overdue=1),
            ]
            check_sla_overdue.run()

        assert mock_alert.delay.call_count == 2
        mock_alert.delay.assert_any_call("coal")
        mock_alert.delay.assert_any_call("microbiology")

    @patch("app.tasks.email_tasks.send_sla_overdue_alert")
    @patch("app.services.sla_service.get_sla_summary", create=True)
    def test_no_alerts_when_none_overdue(self, mock_summary, mock_alert, app):
        with app.app_context():
            from app.tasks.sla_tasks import check_sla_overdue

            mock_summary.return_value = SimpleNamespace(overdue=0)
            check_sla_overdue.run()

        mock_alert.delay.assert_not_called()


# ===========================================================================
# sla_tasks.auto_assign_sla  (unbound)
# ===========================================================================

class TestAutoAssignSla:

    @patch("app.services.sla_service.bulk_assign_sla", create=True)
    def test_assigns_all_lab_types(self, mock_bulk, app):
        with app.app_context():
            from app.tasks.sla_tasks import auto_assign_sla

            mock_bulk.side_effect = [10, 5, 0]
            result = auto_assign_sla.run()

        assert result["assigned"] == 15
        assert mock_bulk.call_count == 3

    @patch("app.services.sla_service.bulk_assign_sla", create=True)
    def test_zero_when_nothing_to_assign(self, mock_bulk, app):
        with app.app_context():
            from app.tasks.sla_tasks import auto_assign_sla

            mock_bulk.return_value = 0
            result = auto_assign_sla.run()

        assert result["assigned"] == 0


# ===========================================================================
# sla_tasks.mark_completed_samples  (unbound, uses real DB)
# ===========================================================================

class TestMarkCompletedSamples:

    def _create_sample(self, db, code, status, completed_at=None):
        from app.models import Sample
        s = Sample(
            sample_code=code, lab_type="coal",
            status=status, completed_at=completed_at,
        )
        db.session.add(s)
        db.session.flush()
        return s

    def _create_result(self, db, sample_id, code, status):
        from app.models import AnalysisResult
        ar = AnalysisResult(
            sample_id=sample_id, analysis_code=code, status=status,
        )
        db.session.add(ar)
        return ar

    def test_marks_fully_approved(self, app, db):
        with app.app_context():
            from app.tasks.sla_tasks import mark_completed_samples

            s = self._create_sample(db, "MRK-T01", "in_progress")
            ar = self._create_result(db, s.id, "Mad", "approved")
            db.session.commit()

            result = mark_completed_samples.run()

            db.session.refresh(s)
            assert s.status == "completed"
            assert s.completed_at is not None
            assert result["marked"] >= 1

            db.session.delete(ar)
            db.session.delete(s)
            db.session.commit()

    def test_skip_pending_review(self, app, db):
        with app.app_context():
            from app.tasks.sla_tasks import mark_completed_samples

            s = self._create_sample(db, "MRK-T02", "in_progress")
            ar = self._create_result(db, s.id, "Mad", "pending_review")
            db.session.commit()

            result = mark_completed_samples.run()

            db.session.refresh(s)
            assert s.status == "in_progress"
            assert s.completed_at is None

            db.session.delete(ar)
            db.session.delete(s)
            db.session.commit()

    def test_skip_no_results(self, app, db):
        with app.app_context():
            from app.tasks.sla_tasks import mark_completed_samples

            s = self._create_sample(db, "MRK-T03", "new")
            db.session.commit()

            result = mark_completed_samples.run()

            db.session.refresh(s)
            assert s.status == "new"

            db.session.delete(s)
            db.session.commit()

    def test_skip_already_completed(self, app, db):
        with app.app_context():
            from app.tasks.sla_tasks import mark_completed_samples
            from app.utils.datetime import now_local

            s = self._create_sample(db, "MRK-T04", "completed", completed_at=now_local())
            ar = self._create_result(db, s.id, "Mad", "approved")
            db.session.commit()

            result = mark_completed_samples.run()
            assert result["marked"] == 0

            db.session.delete(ar)
            db.session.delete(s)
            db.session.commit()

    def test_mixed_not_marked(self, app, db):
        with app.app_context():
            from app.tasks.sla_tasks import mark_completed_samples

            s = self._create_sample(db, "MRK-T05", "in_progress")
            ar1 = self._create_result(db, s.id, "Mad", "approved")
            ar2 = self._create_result(db, s.id, "Aad", "rejected")
            db.session.commit()

            result = mark_completed_samples.run()

            db.session.refresh(s)
            assert s.status == "in_progress"

            db.session.delete(ar1)
            db.session.delete(ar2)
            db.session.delete(s)
            db.session.commit()

    def test_archived_excluded(self, app, db):
        with app.app_context():
            from app.tasks.sla_tasks import mark_completed_samples

            s = self._create_sample(db, "MRK-T06", "archived")
            ar = self._create_result(db, s.id, "Mad", "approved")
            db.session.commit()

            result = mark_completed_samples.run()

            db.session.refresh(s)
            assert s.status == "archived"
            assert result["marked"] == 0

            db.session.delete(ar)
            db.session.delete(s)
            db.session.commit()
