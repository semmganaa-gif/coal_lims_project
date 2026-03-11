# tests/test_reports_coverage_boost.py
# -*- coding: utf-8 -*-
"""Coverage boost tests for reports: pdf_generator, crud, email_sender."""

import os
import smtplib
import uuid
from datetime import datetime, date
from io import BytesIO
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app import db as _db
from app.models import LabReport, ReportSignature, Sample, AnalysisResult, User


# =========================================================================
# Helpers
# =========================================================================

def _make_report(db_session, **overrides):
    """Create and persist a LabReport with sensible defaults."""
    defaults = dict(
        report_number=f"2026_{uuid.uuid4().hex[:6]}",
        lab_type="water",
        report_type="analysis",
        title="Test report",
        status="draft",
        sample_ids=[1],
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 31),
        created_by_id=1,
    )
    defaults.update(overrides)
    r = LabReport(**defaults)
    db_session.add(r)
    db_session.commit()
    return r


def _make_signature(db_session, **overrides):
    """Create a ReportSignature."""
    defaults = dict(
        name="Test Signer",
        signature_type="signature",
        lab_type="all",
        is_active=True,
        position="Analyst",
    )
    defaults.update(overrides)
    s = ReportSignature(**defaults)
    db_session.add(s)
    db_session.commit()
    return s


def _make_sample(db_session, lab_type="water", user_id=1):
    """Create a test Sample."""
    s = Sample(
        sample_code=f"RPT-{uuid.uuid4().hex[:6]}",
        lab_type=lab_type,
        user_id=user_id,
        client_name="QC",
        sample_type="test",
    )
    db_session.add(s)
    db_session.commit()
    return s


def _make_analysis_result(db_session, sample_id, code="PH"):
    """Create an AnalysisResult for a sample."""
    ar = AnalysisResult(
        sample_id=sample_id,
        analysis_code=code,
        status="approved",
    )
    db_session.add(ar)
    db_session.commit()
    return ar


def _login_admin(client):
    client.post("/login", data={"username": "admin", "password": "TestPass123"})


def _login_chemist(client):
    client.post("/login", data={"username": "chemist", "password": "TestPass123"})


def _login_senior(client):
    client.post("/login", data={"username": "senior", "password": "TestPass123"})


# =========================================================================
# pdf_generator tests
# =========================================================================
class TestRegisterFonts:
    """Tests for register_fonts()."""

    def test_register_fonts_first_call(self, app):
        import app.routes.reports.pdf_generator as mod
        mod._font_registered = False  # reset
        with app.app_context():
            with patch("app.routes.reports.pdf_generator.os.path.exists", return_value=True), \
                 patch("app.routes.reports.pdf_generator.pdfmetrics.registerFont"):
                mod.register_fonts()
                assert mod._font_registered is True

    def test_register_fonts_already_registered(self, app):
        import app.routes.reports.pdf_generator as mod
        mod._font_registered = True
        with app.app_context():
            with patch("app.routes.reports.pdf_generator.pdfmetrics.registerFont") as mock_reg:
                mod.register_fonts()
                mock_reg.assert_not_called()
        mod._font_registered = False  # cleanup

    def test_register_fonts_no_font_file(self, app):
        import app.routes.reports.pdf_generator as mod
        mod._font_registered = False
        with app.app_context():
            with patch("app.routes.reports.pdf_generator.os.path.exists", return_value=False):
                mod.register_fonts()
                assert mod._font_registered is False

    def test_register_fonts_oserror(self, app):
        import app.routes.reports.pdf_generator as mod
        mod._font_registered = False
        with app.app_context():
            with patch("app.routes.reports.pdf_generator.os.path.exists", return_value=True), \
                 patch("app.routes.reports.pdf_generator.pdfmetrics.registerFont", side_effect=OSError("bad")):
                mod.register_fonts()
                assert mod._font_registered is False


class TestCreatePdfFromHtml:
    """Tests for create_pdf_from_html()."""

    def test_xhtml2pdf_not_available(self, app):
        import app.routes.reports.pdf_generator as mod
        orig = mod.XHTML2PDF_AVAILABLE
        mod.XHTML2PDF_AVAILABLE = False
        try:
            with pytest.raises(RuntimeError, match="xhtml2pdf"):
                mod.create_pdf_from_html("<html></html>", "/tmp/test.pdf")
        finally:
            mod.XHTML2PDF_AVAILABLE = orig

    def test_create_pdf_success(self, app):
        import app.routes.reports.pdf_generator as mod
        orig = mod.XHTML2PDF_AVAILABLE
        mod.XHTML2PDF_AVAILABLE = True
        mod._font_registered = True  # skip font registration

        mock_pisa_status = MagicMock()
        mock_pisa_status.err = 0

        with app.app_context():
            with patch("app.routes.reports.pdf_generator.pisa") as mock_pisa, \
                 patch("builtins.open", MagicMock()):
                mock_pisa.CreatePDF.return_value = mock_pisa_status
                result = mod.create_pdf_from_html("<html></html>", "/tmp/out.pdf")
                assert result is True

        mod.XHTML2PDF_AVAILABLE = orig
        mod._font_registered = False

    def test_create_pdf_with_errors(self, app):
        import app.routes.reports.pdf_generator as mod
        orig = mod.XHTML2PDF_AVAILABLE
        mod.XHTML2PDF_AVAILABLE = True
        mod._font_registered = True

        mock_pisa_status = MagicMock()
        mock_pisa_status.err = 1

        with app.app_context():
            with patch("app.routes.reports.pdf_generator.pisa") as mock_pisa, \
                 patch("builtins.open", MagicMock()):
                mock_pisa.CreatePDF.return_value = mock_pisa_status
                result = mod.create_pdf_from_html("<html></html>", "/tmp/out.pdf")
                assert result is False

        mod.XHTML2PDF_AVAILABLE = orig
        mod._font_registered = False


class TestGeneratePdfFile:
    """Tests for generate_pdf_file()."""

    def test_generate_pdf_file_basic(self, app):
        import app.routes.reports.pdf_generator as mod

        report = MagicMock()
        report.report_number = "2026_1"
        report.lab_type = "water"

        with app.app_context():
            with patch("app.routes.reports.pdf_generator.os.makedirs"), \
                 patch("app.routes.reports.pdf_generator.os.path.exists", return_value=False), \
                 patch("app.routes.reports.pdf_generator.render_template", return_value="<html></html>"), \
                 patch("app.routes.reports.pdf_generator.create_pdf_from_html"):
                path = mod.generate_pdf_file(report, [], [])
                assert "2026_1.pdf" in path
                assert path.startswith("uploads/reports/")

    def test_generate_pdf_file_with_logos(self, app):
        import app.routes.reports.pdf_generator as mod

        report = MagicMock()
        report.report_number = "2026_2"
        report.lab_type = "coal"

        with app.app_context():
            with patch("app.routes.reports.pdf_generator.os.makedirs"), \
                 patch("app.routes.reports.pdf_generator.os.path.exists", return_value=True), \
                 patch("app.routes.reports.pdf_generator.render_template", return_value="<html></html>") as mock_rt, \
                 patch("app.routes.reports.pdf_generator.create_pdf_from_html"):
                mod.generate_pdf_file(report, [], [])
                call_kwargs = mock_rt.call_args[1]
                assert call_kwargs["company_logo"] is not None
                assert call_kwargs["mnas_logo"] is not None


class TestGenerateReportFunctions:
    """Tests for generate_microbiology_report, generate_water_report, generate_coal_report."""

    def test_generate_microbiology_report_no_samples(self, app):
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            with patch.object(Sample, "query") as mock_q:
                mock_q.filter.return_value.order_by.return_value.all.return_value = []
                report, error = mod.generate_microbiology_report([999], None, None, 1)
                assert report is None
                assert error == "Sample not found"

    def test_generate_water_report_no_samples(self, app):
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            with patch.object(Sample, "query") as mock_q:
                mock_q.filter.return_value.order_by.return_value.all.return_value = []
                report, error = mod.generate_water_report([999], None, None, 1)
                assert report is None
                assert error == "Sample not found"

    def test_generate_coal_report_no_samples(self, app):
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            with patch.object(Sample, "query") as mock_q:
                mock_q.filter.return_value.order_by.return_value.all.return_value = []
                report, error = mod.generate_coal_report([999], None, None, 1)
                assert report is None
                assert error == "Sample not found"

    def test_generate_water_report_success(self, app, db):
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            user = User.query.filter_by(username="chemist").first()
            sample = _make_sample(_db.session, lab_type="water", user_id=user.id)
            _make_analysis_result(_db.session, sample.id, "PH")

            with patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="uploads/reports/test.pdf"):
                report, error = mod.generate_water_report(
                    [sample.id], date(2026, 1, 1), date(2026, 1, 31), user.id
                )
                assert error is None
                assert report is not None
                assert report.lab_type == "water"
                assert report.status == "draft"

            # cleanup
            _db.session.delete(report)
            _db.session.delete(sample)
            _db.session.commit()

    def test_generate_coal_report_success(self, app, db):
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            user = User.query.filter_by(username="chemist").first()
            sample = _make_sample(_db.session, lab_type="coal", user_id=user.id)

            with patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="uploads/reports/coal.pdf"):
                report, error = mod.generate_coal_report(
                    [sample.id], date(2026, 1, 1), date(2026, 1, 31), user.id
                )
                assert error is None
                assert report is not None
                assert report.lab_type == "coal"

            _db.session.delete(report)
            _db.session.delete(sample)
            _db.session.commit()

    def test_generate_microbiology_report_success(self, app, db):
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            user = User.query.filter_by(username="chemist").first()
            sample = _make_sample(_db.session, lab_type="microbiology", user_id=user.id)
            _make_analysis_result(_db.session, sample.id, "MICRO_WATER")

            with patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="uploads/reports/micro.pdf"):
                report, error = mod.generate_microbiology_report(
                    [sample.id], None, None, user.id
                )
                assert error is None
                assert report is not None
                assert report.lab_type == "microbiology"

            _db.session.delete(report)
            _db.session.delete(sample)
            _db.session.commit()

    def test_generate_water_report_commit_error(self, app, db):
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            user = User.query.filter_by(username="chemist").first()
            sample = _make_sample(_db.session, lab_type="water", user_id=user.id)

            with patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="x.pdf"), \
                 patch("app.routes.reports.pdf_generator.db.session.commit", side_effect=SQLAlchemyError("fail")), \
                 patch("app.routes.reports.pdf_generator.db.session.rollback"):
                report, error = mod.generate_water_report(
                    [sample.id], None, None, user.id
                )
                assert report is None
                assert error is not None

            _db.session.rollback()
            _db.session.delete(sample)
            _db.session.commit()

    def test_generate_coal_report_commit_error(self, app, db):
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            user = User.query.filter_by(username="chemist").first()
            sample = _make_sample(_db.session, lab_type="coal", user_id=user.id)

            with patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="x.pdf"), \
                 patch("app.routes.reports.pdf_generator.db.session.commit", side_effect=SQLAlchemyError("fail")), \
                 patch("app.routes.reports.pdf_generator.db.session.rollback"):
                report, error = mod.generate_coal_report(
                    [sample.id], None, None, user.id
                )
                assert report is None
                assert error is not None

            _db.session.rollback()
            _db.session.delete(sample)
            _db.session.commit()

    def test_generate_microbiology_report_commit_error(self, app, db):
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            user = User.query.filter_by(username="chemist").first()
            sample = _make_sample(_db.session, lab_type="microbiology", user_id=user.id)

            with patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="x.pdf"), \
                 patch("app.routes.reports.pdf_generator.db.session.commit", side_effect=SQLAlchemyError("fail")), \
                 patch("app.routes.reports.pdf_generator.db.session.rollback"):
                report, error = mod.generate_microbiology_report(
                    [sample.id], None, None, user.id
                )
                assert report is None
                assert error is not None

            _db.session.rollback()
            _db.session.delete(sample)
            _db.session.commit()

    def test_generate_report_with_date_isoformat(self, app, db):
        """Ensure date_from/date_to isoformat is used in report_data."""
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            user = User.query.filter_by(username="chemist").first()
            sample = _make_sample(_db.session, lab_type="water", user_id=user.id)

            with patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="x.pdf"):
                report, error = mod.generate_water_report(
                    [sample.id], date(2026, 3, 1), date(2026, 3, 15), user.id
                )
                assert error is None
                assert report.report_data["date_from"] == "2026-03-01"
                assert report.report_data["date_to"] == "2026-03-15"

            _db.session.delete(report)
            _db.session.delete(sample)
            _db.session.commit()


class TestRegeneratePdf:
    """Tests for regenerate_pdf()."""

    def test_regenerate_pdf_success(self, app, db):
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            report = _make_report(_db.session, sample_ids=[])
            with patch("app.routes.reports.pdf_generator.os.makedirs"), \
                 patch("app.routes.reports.pdf_generator.os.path.exists", return_value=False), \
                 patch("app.routes.reports.pdf_generator.render_template", return_value="<html></html>"), \
                 patch("app.routes.reports.pdf_generator.create_pdf_from_html"):
                mod.regenerate_pdf(report)
                assert report.pdf_path is not None

            _db.session.delete(report)
            _db.session.commit()

    def test_regenerate_pdf_commit_error(self, app, db):
        import app.routes.reports.pdf_generator as mod
        with app.app_context():
            report = _make_report(_db.session, sample_ids=[])
            with patch("app.routes.reports.pdf_generator.os.makedirs"), \
                 patch("app.routes.reports.pdf_generator.os.path.exists", return_value=False), \
                 patch("app.routes.reports.pdf_generator.render_template", return_value="<html></html>"), \
                 patch("app.routes.reports.pdf_generator.create_pdf_from_html"), \
                 patch("app.routes.reports.pdf_generator.db.session.commit", side_effect=SQLAlchemyError("fail")), \
                 patch("app.routes.reports.pdf_generator.db.session.rollback"):
                mod.regenerate_pdf(report)  # should not raise

            _db.session.rollback()
            _db.session.delete(report)
            _db.session.commit()


# =========================================================================
# crud.py tests
# =========================================================================
class TestGetNextReportNumber:
    """Tests for get_next_report_number()."""

    def test_no_existing_reports(self, app, db):
        from app.routes.reports.crud import get_next_report_number
        with app.app_context():
            with patch.object(LabReport, "query") as mock_q:
                # first() returns None (no last report)
                mock_q.filter.return_value.order_by.return_value.first.return_value = None
                # count returns 0
                mock_q.filter.return_value.count.return_value = 0
                result = get_next_report_number("water")
                year = datetime.now().year
                assert result == f"{year}_1"

    def test_existing_report_increment(self, app, db):
        from app.routes.reports.crud import get_next_report_number
        year = datetime.now().year
        with app.app_context():
            mock_report = MagicMock()
            mock_report.report_number = f"{year}_5"
            with patch.object(LabReport, "query") as mock_q:
                mock_q.filter.return_value.order_by.return_value.first.return_value = mock_report
                result = get_next_report_number("coal")
                assert result == f"{year}_6"

    def test_malformed_report_number_fallback(self, app, db):
        from app.routes.reports.crud import get_next_report_number
        year = datetime.now().year
        with app.app_context():
            mock_report = MagicMock()
            mock_report.report_number = "badformat"
            with patch.object(LabReport, "query") as mock_q:
                mock_q.filter.return_value.order_by.return_value.first.return_value = mock_report
                mock_q.filter.return_value.count.return_value = 3
                result = get_next_report_number("coal")
                assert result == f"{year}_4"


class TestReportListRoute:
    """Tests for report_list route."""

    def test_report_list_unauthenticated(self, client):
        resp = client.get("/pdf-reports/")
        assert resp.status_code in (302, 401)

    def test_report_list_authenticated(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.get("/pdf-reports/")
            assert resp.status_code == 200

    def test_report_list_filter_lab(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.get("/pdf-reports/?lab=water&status=draft")
            assert resp.status_code == 200


class TestSignatureRoutes:
    """Tests for signature CRUD routes."""

    def test_signature_list_no_permission(self, client, app):
        _login_chemist(client)
        with app.app_context():
            resp = client.get("/pdf-reports/signatures", follow_redirects=True)
            assert resp.status_code == 200

    def test_signature_list_admin(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.get("/pdf-reports/signatures")
            assert resp.status_code == 200

    def test_add_signature_get_no_permission(self, client, app):
        _login_chemist(client)
        with app.app_context():
            resp = client.get("/pdf-reports/signatures/add", follow_redirects=True)
            assert resp.status_code == 200

    def test_add_signature_get_admin(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.get("/pdf-reports/signatures/add")
            assert resp.status_code == 200

    def test_add_signature_post_no_file(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.post("/pdf-reports/signatures/add", data={
                "signature_type": "signature",
                "name": "Test Signer",
                "position": "Manager",
                "lab_type": "all",
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_add_signature_post_bad_extension(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            data = {
                "signature_type": "signature",
                "name": "Test",
                "position": "Mgr",
                "lab_type": "all",
                "image": (BytesIO(b"fake"), "test.exe"),
            }
            resp = client.post(
                "/pdf-reports/signatures/add",
                data=data,
                content_type="multipart/form-data",
                follow_redirects=True,
            )
            assert resp.status_code == 200

    def test_add_signature_post_file_too_large(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            # 6MB file
            big_data = b"\x89PNG" + b"\x00" * (6 * 1024 * 1024)
            data = {
                "signature_type": "signature",
                "name": "Test",
                "position": "Mgr",
                "lab_type": "all",
                "image": (BytesIO(big_data), "test.png"),
            }
            resp = client.post(
                "/pdf-reports/signatures/add",
                data=data,
                content_type="multipart/form-data",
                follow_redirects=True,
            )
            assert resp.status_code == 200

    def test_add_signature_post_bad_magic(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            data = {
                "signature_type": "signature",
                "name": "Test",
                "position": "Mgr",
                "lab_type": "all",
                "image": (BytesIO(b"\x00\x00\x00\x00\x00\x00\x00\x00"), "test.png"),
            }
            resp = client.post(
                "/pdf-reports/signatures/add",
                data=data,
                content_type="multipart/form-data",
                follow_redirects=True,
            )
            assert resp.status_code == 200

    def test_add_signature_post_valid_image(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            # PNG magic bytes
            png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
            data = {
                "signature_type": "stamp",
                "name": "Lab Stamp",
                "position": "Lab",
                "lab_type": "water",
                "image": (BytesIO(png_data), "stamp.png"),
            }
            with patch("app.routes.reports.crud.os.makedirs"), \
                 patch("app.routes.reports.crud.os.path.join", side_effect=os.path.join):
                resp = client.post(
                    "/pdf-reports/signatures/add",
                    data=data,
                    content_type="multipart/form-data",
                    follow_redirects=True,
                )
                assert resp.status_code == 200

    def test_delete_signature_no_permission(self, client, app, db):
        _login_chemist(client)
        with app.app_context():
            resp = client.post("/pdf-reports/signatures/delete/999", follow_redirects=True)
            assert resp.status_code == 200

    def test_delete_signature_not_found(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.post("/pdf-reports/signatures/delete/99999")
            assert resp.status_code == 404

    def test_delete_signature_success(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            sig = _make_signature(_db.session, name="ToDelete")
            resp = client.post(f"/pdf-reports/signatures/delete/{sig.id}", follow_redirects=True)
            assert resp.status_code == 200
            updated = _db.session.get(ReportSignature, sig.id)
            assert updated.is_active is False
            _db.session.delete(updated)
            _db.session.commit()


class TestReportDetailRoute:
    """Tests for report_detail route."""

    def test_report_detail_not_found(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.get("/pdf-reports/99999")
            assert resp.status_code == 404

    def test_report_detail_success(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session)
            resp = client.get(f"/pdf-reports/{report.id}")
            assert resp.status_code == 200
            _db.session.delete(report)
            _db.session.commit()


class TestApproveReportRoute:
    """Tests for approve_report route."""

    def test_approve_no_permission(self, client, app, db):
        _login_chemist(client)
        with app.app_context():
            report = _make_report(_db.session)
            resp = client.post(f"/pdf-reports/{report.id}/approve", follow_redirects=True)
            assert resp.status_code == 200
            _db.session.delete(report)
            _db.session.commit()

    def test_approve_not_found(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.post("/pdf-reports/99999/approve")
            assert resp.status_code == 404

    def test_approve_success(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session)
            sig = _make_signature(_db.session, name="Analyst Sig")
            stamp = _make_signature(_db.session, name="Stamp", signature_type="stamp")

            with patch("app.routes.reports.pdf_generator.regenerate_pdf"):
                resp = client.post(
                    f"/pdf-reports/{report.id}/approve",
                    data={
                        "analyst_signature_id": str(sig.id),
                        "manager_signature_id": str(sig.id),
                        "stamp_id": str(stamp.id),
                    },
                    follow_redirects=True,
                )
                assert resp.status_code == 200
                updated = _db.session.get(LabReport, report.id)
                assert updated.status == "approved"

            _db.session.delete(report)
            _db.session.delete(sig)
            _db.session.delete(stamp)
            _db.session.commit()


class TestDownloadReportRoute:
    """Tests for download_report route."""

    def test_download_not_found(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.get("/pdf-reports/99999/download")
            assert resp.status_code == 404

    def test_download_no_pdf_path(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session, pdf_path=None)
            resp = client.get(f"/pdf-reports/{report.id}/download", follow_redirects=True)
            assert resp.status_code == 200
            _db.session.delete(report)
            _db.session.commit()

    def test_download_path_traversal(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session, pdf_path="../../etc/passwd")
            resp = client.get(f"/pdf-reports/{report.id}/download", follow_redirects=True)
            assert resp.status_code == 200  # redirects with flash
            _db.session.delete(report)
            _db.session.commit()

    def test_download_file_not_exists(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session, pdf_path="uploads/reports/nonexistent.pdf")
            resp = client.get(f"/pdf-reports/{report.id}/download", follow_redirects=True)
            assert resp.status_code == 200  # redirects
            _db.session.delete(report)
            _db.session.commit()


class TestDeleteReportRoute:
    """Tests for delete_report route."""

    def test_delete_no_permission(self, client, app, db):
        _login_chemist(client)
        with app.app_context():
            resp = client.post("/pdf-reports/1/delete", follow_redirects=True)
            assert resp.status_code == 200

    def test_delete_not_found(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.post("/pdf-reports/99999/delete")
            assert resp.status_code == 404

    def test_delete_success_no_pdf(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session, pdf_path=None)
            rid = report.id
            resp = client.post(f"/pdf-reports/{rid}/delete", follow_redirects=True)
            assert resp.status_code == 200
            assert _db.session.get(LabReport, rid) is None

    def test_delete_success_with_pdf(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session, pdf_path="uploads/reports/del.pdf")
            rid = report.id
            with patch("app.routes.reports.crud.os.path.exists", return_value=True), \
                 patch("app.routes.reports.crud.os.remove"):
                resp = client.post(f"/pdf-reports/{rid}/delete", follow_redirects=True)
                assert resp.status_code == 200


class TestApiCreateReport:
    """Tests for api_create_report route."""

    def test_api_create_unauthenticated(self, client):
        resp = client.post("/pdf-reports/api/create", json={"lab_type": "water", "sample_ids": [1]})
        assert resp.status_code in (302, 401)

    def test_api_create_missing_fields(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.post("/pdf-reports/api/create", json={"lab_type": "", "sample_ids": []})
            assert resp.status_code == 400
            data = resp.get_json()
            assert data["success"] is False

    def test_api_create_bad_date(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.post("/pdf-reports/api/create", json={
                "lab_type": "water",
                "sample_ids": [1],
                "date_from": "not-a-date",
            })
            assert resp.status_code == 400

    def test_api_create_unknown_lab_type(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.post("/pdf-reports/api/create", json={
                "lab_type": "unknown",
                "sample_ids": [1],
            })
            assert resp.status_code == 400
            assert "Тодорхойгүй" in resp.get_json()["error"]

    def test_api_create_water_success(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            mock_report = MagicMock()
            mock_report.id = 1
            mock_report.report_number = "2026_1"
            with patch("app.routes.reports.pdf_generator.generate_water_report", return_value=(mock_report, None)):
                resp = client.post("/pdf-reports/api/create", json={
                    "lab_type": "water",
                    "sample_ids": [1],
                    "date_from": "2026-01-01",
                    "date_to": "2026-01-31",
                })
                assert resp.status_code == 200
                assert resp.get_json()["success"] is True

    def test_api_create_coal_success(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            mock_report = MagicMock()
            mock_report.id = 2
            mock_report.report_number = "2026_2"
            with patch("app.routes.reports.pdf_generator.generate_coal_report", return_value=(mock_report, None)):
                resp = client.post("/pdf-reports/api/create", json={
                    "lab_type": "coal",
                    "sample_ids": [1],
                })
                assert resp.status_code == 200

    def test_api_create_microbiology_success(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            mock_report = MagicMock()
            mock_report.id = 3
            mock_report.report_number = "2026_3"
            with patch("app.routes.reports.pdf_generator.generate_microbiology_report", return_value=(mock_report, None)):
                resp = client.post("/pdf-reports/api/create", json={
                    "lab_type": "microbiology",
                    "sample_ids": [1],
                })
                assert resp.status_code == 200

    def test_api_create_generator_error(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            with patch("app.routes.reports.pdf_generator.generate_water_report", return_value=(None, "Some error")):
                resp = client.post("/pdf-reports/api/create", json={
                    "lab_type": "water",
                    "sample_ids": [1],
                })
                assert resp.status_code == 400
                assert resp.get_json()["success"] is False

    def test_api_create_exception(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            with patch("app.routes.reports.pdf_generator.generate_water_report", side_effect=SQLAlchemyError("boom")):
                resp = client.post("/pdf-reports/api/create", json={
                    "lab_type": "water",
                    "sample_ids": [1],
                })
                assert resp.status_code == 500


# =========================================================================
# email_sender.py tests
# =========================================================================
class TestSendReportEmail:
    """Tests for send_report_email()."""

    def test_missing_smtp_credentials(self, app):
        from app.routes.reports.email_sender import send_report_email
        with app.app_context():
            app.config["MAIL_USERNAME"] = None
            app.config["MAIL_PASSWORD"] = None
            report = MagicMock()
            success, error = send_report_email(report, ["test@test.com"])
            assert success is False
            assert "SMTP" in error

    def test_send_success_no_pdf(self, app):
        from app.routes.reports.email_sender import send_report_email
        with app.app_context():
            app.config["MAIL_USERNAME"] = "user@test.com"
            app.config["MAIL_PASSWORD"] = "pass"
            app.config["MAIL_SERVER"] = "smtp.test.com"
            app.config["MAIL_PORT"] = 587

            report = MagicMock()
            report.pdf_path = None
            report.report_number = "2026_1"
            report.title = "Test"
            report.date_from = "2026-01-01"
            report.date_to = "2026-01-31"

            with patch("app.routes.reports.email_sender.smtplib.SMTP") as mock_smtp:
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
                mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
                success, error = send_report_email(report, ["a@b.com"])
                assert success is True
                assert error is None

    def test_send_success_with_pdf(self, app):
        from app.routes.reports.email_sender import send_report_email
        with app.app_context():
            app.config["MAIL_USERNAME"] = "user@test.com"
            app.config["MAIL_PASSWORD"] = "pass"

            report = MagicMock()
            report.pdf_path = "uploads/reports/test.pdf"
            report.report_number = "2026_1"
            report.title = "Test"
            report.date_from = "2026-01-01"
            report.date_to = "2026-01-31"

            with patch("app.routes.reports.email_sender.smtplib.SMTP") as mock_smtp, \
                 patch("app.routes.reports.email_sender.os.path.exists", return_value=True), \
                 patch("builtins.open", MagicMock(return_value=BytesIO(b"pdf_data"))):
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
                mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
                success, error = send_report_email(
                    report, ["a@b.com"], subject="Custom", body="Custom body"
                )
                assert success is True

    def test_send_auth_error(self, app):
        from app.routes.reports.email_sender import send_report_email
        with app.app_context():
            app.config["MAIL_USERNAME"] = "user@test.com"
            app.config["MAIL_PASSWORD"] = "bad"

            report = MagicMock()
            report.pdf_path = None
            report.report_number = "2026_1"
            report.title = "Test"
            report.date_from = None
            report.date_to = None

            with patch("app.routes.reports.email_sender.smtplib.SMTP") as mock_smtp:
                mock_server = MagicMock()
                mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad creds")
                mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
                mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
                success, error = send_report_email(report, ["a@b.com"])
                assert success is False
                assert "нэвтрэлт" in error

    def test_send_smtp_exception(self, app):
        from app.routes.reports.email_sender import send_report_email
        with app.app_context():
            app.config["MAIL_USERNAME"] = "user@test.com"
            app.config["MAIL_PASSWORD"] = "pass"

            report = MagicMock()
            report.pdf_path = None
            report.report_number = "2026_1"
            report.title = "Test"
            report.date_from = None
            report.date_to = None

            with patch("app.routes.reports.email_sender.smtplib.SMTP") as mock_smtp:
                mock_server = MagicMock()
                mock_server.send_message.side_effect = smtplib.SMTPException("conn lost")
                mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
                mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
                success, error = send_report_email(report, ["a@b.com"])
                assert success is False
                assert "SMTP" in error

    def test_send_os_error(self, app):
        from app.routes.reports.email_sender import send_report_email
        with app.app_context():
            app.config["MAIL_USERNAME"] = "user@test.com"
            app.config["MAIL_PASSWORD"] = "pass"

            report = MagicMock()
            report.pdf_path = "uploads/test.pdf"
            report.report_number = "2026_1"
            report.title = "Test"
            report.date_from = None
            report.date_to = None

            with patch("app.routes.reports.email_sender.smtplib.SMTP", side_effect=OSError("network down")):
                success, error = send_report_email(report, ["a@b.com"])
                assert success is False
                assert "Error" in error


class TestSendEmailRoute:
    """Tests for the send_email route."""

    def test_send_email_no_permission(self, client, app, db):
        _login_chemist(client)
        with app.app_context():
            report = _make_report(_db.session, status="approved")
            resp = client.get(f"/pdf-reports/{report.id}/send_email", follow_redirects=True)
            assert resp.status_code == 200
            _db.session.delete(report)
            _db.session.commit()

    def test_send_email_not_found(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            resp = client.get("/pdf-reports/99999/send_email")
            assert resp.status_code == 404

    def test_send_email_not_approved(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session, status="draft")
            resp = client.get(f"/pdf-reports/{report.id}/send_email", follow_redirects=True)
            assert resp.status_code == 200
            _db.session.delete(report)
            _db.session.commit()

    def test_send_email_get_form(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session, status="approved")
            resp = client.get(f"/pdf-reports/{report.id}/send_email")
            assert resp.status_code == 200
            _db.session.delete(report)
            _db.session.commit()

    def test_send_email_post_no_recipients(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session, status="approved")
            resp = client.post(
                f"/pdf-reports/{report.id}/send_email",
                data={"recipients": ""},
                follow_redirects=True,
            )
            assert resp.status_code == 200
            _db.session.delete(report)
            _db.session.commit()

    def test_send_email_post_success(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session, status="approved")
            with patch("app.routes.reports.email_sender.send_report_email", return_value=(True, None)):
                resp = client.post(
                    f"/pdf-reports/{report.id}/send_email",
                    data={
                        "recipients": "test@test.com, admin@test.com",
                        "subject": "Test Subject",
                        "body": "Test Body",
                    },
                    follow_redirects=True,
                )
                assert resp.status_code == 200
                updated = _db.session.get(LabReport, report.id)
                assert updated.status == "sent"
                assert updated.email_sent is True

            _db.session.delete(report)
            _db.session.commit()

    def test_send_email_post_failure(self, client, app, db):
        _login_admin(client)
        with app.app_context():
            report = _make_report(_db.session, status="approved")
            with patch("app.routes.reports.email_sender.send_report_email", return_value=(False, "SMTP error")):
                resp = client.post(
                    f"/pdf-reports/{report.id}/send_email",
                    data={"recipients": "test@test.com"},
                    follow_redirects=True,
                )
                assert resp.status_code == 200

            _db.session.delete(report)
            _db.session.commit()


class TestImageValidation:
    """Tests for signature image validation constants and flows."""

    def test_allowed_extensions(self):
        from app.routes.reports.crud import ALLOWED_IMAGE_EXTENSIONS
        assert "png" in ALLOWED_IMAGE_EXTENSIONS
        assert "jpg" in ALLOWED_IMAGE_EXTENSIONS
        assert "exe" not in ALLOWED_IMAGE_EXTENSIONS

    def test_max_file_size(self):
        from app.routes.reports.crud import MAX_SIGNATURE_FILE_SIZE
        assert MAX_SIGNATURE_FILE_SIZE == 5 * 1024 * 1024

    def test_magic_bytes_keys(self):
        from app.routes.reports.crud import IMAGE_MAGIC_BYTES
        assert b"\x89PNG" in IMAGE_MAGIC_BYTES
        assert b"\xff\xd8\xff" in IMAGE_MAGIC_BYTES
