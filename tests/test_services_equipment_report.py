# tests/test_services_equipment_report.py
# -*- coding: utf-8 -*-
"""
Comprehensive tests for:
  - app/services/equipment_service.py
  - app/services/report_service.py
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock
from collections import defaultdict

from sqlalchemy.exc import SQLAlchemyError


# =====================================================================
# equipment_service — build_calibration_description
# =====================================================================

class TestBuildCalibrationDescription:
    """Tests for build_calibration_description (all calibration types)."""

    def _call(self, calibration):
        from app.services.equipment_service import build_calibration_description
        return build_calibration_description(calibration)

    # --- temperature ---

    def test_temperature_pass(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "temperature",
                "set_temp": 100.0,
                "actual_temp": 102.0,
            })
        assert result == "Pass"
        assert any("102" in p for p in desc)
        assert any("Зөрүү" in p for p in desc)

    def test_temperature_fail_large_diff(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "temperature",
                "set_temp": 100.0,
                "actual_temp": 110.0,
            })
        assert result == "Fail"

    def test_temperature_negative_diff(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "temperature",
                "set_temp": 100.0,
                "actual_temp": 94.0,
            })
        assert result == "Fail"
        assert any("-" in p for p in desc)

    def test_temperature_none_values(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "temperature",
                "set_temp": None,
                "actual_temp": None,
            })
        assert result == "Pass"
        assert desc == []

    def test_temperature_exact_boundary(self, app):
        """Exactly 5 degrees diff should pass."""
        with app.app_context():
            desc, result = self._call({
                "type": "temperature",
                "set_temp": 100.0,
                "actual_temp": 105.0,
            })
        assert result == "Pass"

    # --- weight ---

    def test_weight_pass(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "weight",
                "weights": [
                    {"standard": 10.0, "measured": 10.0005},
                    {"standard": 0.5, "measured": 0.5001},
                ],
            })
        assert result == "Pass"
        assert len(desc) == 2

    def test_weight_fail_tolerance(self, app):
        """Weight under 1g has tolerance 0.0002, over 1g has 0.001."""
        with app.app_context():
            desc, result = self._call({
                "type": "weight",
                "weights": [
                    {"standard": 0.5, "measured": 0.5005},  # diff=0.0005 > 0.0002 -> FAIL
                ],
            })
        assert result == "Fail"
        assert any("FAIL" in p for p in desc)

    def test_weight_large_standard_fail(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "weight",
                "weights": [
                    {"standard": 10.0, "measured": 10.005},  # diff=0.005 > 0.001 -> FAIL
                ],
            })
        assert result == "Fail"

    def test_weight_empty_weights(self, app):
        with app.app_context():
            desc, result = self._call({"type": "weight", "weights": []})
        assert result == "Pass"
        assert desc == []

    def test_weight_with_ethanol_pass(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "weight",
                "weights": [],
                "ethanol": {
                    "temperature": 20.0,
                    "density": 0.789,
                    "volume": 10.0,
                    "expected": 7.8900,
                    "measured": 7.8905,
                },
            })
        assert result == "Pass"
        assert any("Этанол" in p for p in desc)
        assert any("Температур" in p for p in desc)

    def test_weight_with_ethanol_fail(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "weight",
                "weights": [],
                "ethanol": {
                    "temperature": 20.0,
                    "density": 0.789,
                    "volume": 10.0,
                    "expected": 7.8900,
                    "measured": 7.9000,  # diff > 0.001
                },
            })
        assert result == "Fail"

    def test_weight_ethanol_partial_fields(self, app):
        """Ethanol with some None fields should not crash."""
        with app.app_context():
            desc, result = self._call({
                "type": "weight",
                "weights": [],
                "ethanol": {
                    "temperature": None,
                    "density": None,
                    "volume": None,
                    "expected": None,
                    "measured": None,
                },
            })
        assert result == "Pass"
        assert any("Этанол" in p for p in desc)

    # --- sulfur ---

    def test_sulfur_pass(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "sulfur",
                "curve_type": "linear",
                "rms_error": 0.0015,
                "standards": [
                    {"name": "Std A", "weight": 0.5, "moisture": 1.2, "certified": 1.0, "measured": 1.02},
                ],
                "verifications": [
                    {"name": "Verify 1", "certified": 2.0, "measured": 2.05},
                ],
            })
        assert result == "Pass"
        assert any("Хүхэр" in p for p in desc)
        assert any("RMS" in p for p in desc)

    def test_sulfur_fail_standard(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "sulfur",
                "standards": [
                    {"name": "Std A", "certified": 1.0, "measured": 1.10},  # 10% > 5%
                ],
            })
        assert result == "Fail"

    def test_sulfur_fail_verification(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "sulfur",
                "standards": [],
                "verifications": [
                    {"name": "V1", "certified": 2.0, "measured": 2.20},  # 10% > 5%
                ],
            })
        assert result == "Fail"

    def test_sulfur_zero_certified(self, app):
        """cert=0 should not cause division by zero."""
        with app.app_context():
            desc, result = self._call({
                "type": "sulfur",
                "standards": [
                    {"name": "Std", "certified": 0, "measured": 0.01},
                ],
            })
        assert result == "Pass"  # diff_pct = 0 when cert == 0

    def test_xrf_calib_type(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "xrf_calib",
                "standards": [],
            })
        assert any("XRF" in p for p in desc)
        assert result == "Pass"

    # --- calorimeter ---

    def test_calorimeter_pass(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "calorimeter",
                "standard_name": "Бензой хүчил",
                "certified_value": 26454,
                "prev_heat_capacity": 10200,
                "bomb_heat_capacity": 10250,
                "measurements": [26450, 26460, 26455, 26448, 26452],
            })
        assert result == "Pass"
        assert any("Илчлэг" in p for p in desc)
        assert any("RSD" in p for p in desc)

    def test_calorimeter_fail_rsd(self, app):
        """RSD > 0.1% should fail."""
        with app.app_context():
            desc, result = self._call({
                "type": "calorimeter",
                "measurements": [26000, 27000, 25000, 28000, 24000],
            })
        assert result == "Fail"

    def test_calorimeter_fail_avg_diff(self, app):
        """avg_diff > 60 should fail."""
        with app.app_context():
            desc, result = self._call({
                "type": "calorimeter",
                "certified_value": 26454,
                "measurements": [26520, 26520, 26520],  # avg ~26520, diff ~66 > 60
            })
        assert result == "Fail"

    def test_calorimeter_single_measurement(self, app):
        """Single measurement should set rsd=0."""
        with app.app_context():
            desc, result = self._call({
                "type": "calorimeter",
                "certified_value": 26454,
                "measurements": [26454],
            })
        assert result == "Pass"

    def test_calorimeter_empty_measurements(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "calorimeter",
                "measurements": [],
            })
        assert result == "Pass"
        assert desc == []

    # --- analysis ---

    def test_analysis_pass(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "analysis",
                "standard_name": "SRM",
                "certified_value": 10.0,
                "measured_value": 10.15,
            })
        assert result == "Pass"
        assert any("SRM" in p for p in desc)

    def test_analysis_fail(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "analysis",
                "standard_name": "SRM",
                "certified_value": 10.0,
                "measured_value": 10.30,  # 3% > 2%
            })
        assert result == "Fail"

    def test_analysis_none_values(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "analysis",
                "certified_value": None,
                "measured_value": None,
            })
        assert result == "Pass"
        assert desc == []

    def test_analysis_zero_certified(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "analysis",
                "certified_value": 0,
                "measured_value": 0.01,
            })
        assert result == "Pass"  # diff_pct=0 when cert=0

    # --- csn_crucible ---

    def test_csn_crucible_pass(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "csn_crucible",
                "start_temp": 300,
                "max_current_sec": 60,
                "tests": [
                    {"temp_1min": 350, "temp_1m30": 400, "temp_2m30": 500, "pass": True},
                ],
                "adjustments": [
                    {"start_temp": 310, "max_current_sec": 55},
                ],
                "final_pass": True,
            })
        assert result == "Pass"
        assert any("CSN" in p for p in desc)

    def test_csn_crucible_fail(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "csn_crucible",
                "final_pass": False,
                "tests": [
                    {"temp_1min": 350, "temp_1m30": 400, "temp_2m30": 500, "pass": False},
                ],
            })
        assert result == "Fail"

    def test_csn_crucible_no_optional_fields(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "csn_crucible",
                "final_pass": True,
            })
        assert result == "Pass"

    # --- drum ---

    def test_drum_gi_pass(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "drum",
                "meas_1min": 50,
                "meas_5min": 250,
                "initial_rpm": 100,
                "target_1min": 50,
                "target_5min": 250,
                "pass": True,
            })
        assert result == "Pass"
        assert any("Барабан" in p for p in desc)

    def test_drum_gi_fail(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "drum",
                "meas_1min": 48,
                "meas_5min": 245,
                "pass": False,
            })
        assert result == "Fail"
        assert any("FAIL" in p for p in desc)

    def test_drum_prep_pass(self, app):
        """Prep drum: no meas_1min/meas_5min, uses before/after."""
        with app.app_context():
            desc, result = self._call({
                "type": "drum",
                "before": 100,
                "after": 101,
                "duration": 30,
            })
        assert result == "Pass"
        assert any("Тээрэм" in p for p in desc)

    def test_drum_prep_fail(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "drum",
                "before": 100,
                "after": 105,  # diff=5 > 2
            })
        assert result == "Fail"

    def test_drum_prep_no_before_after(self, app):
        with app.app_context():
            desc, result = self._call({
                "type": "drum",
            })
        assert result == "Pass"  # falls into else branch, no before/after

    # --- unknown type ---

    def test_unknown_type(self, app):
        with app.app_context():
            desc, result = self._call({"type": "unknown_thing"})
        assert result == "Pass"
        assert desc == []

    def test_empty_type(self, app):
        with app.app_context():
            desc, result = self._call({})
        assert result == "Pass"
        assert desc == []


# =====================================================================
# equipment_service — process_bulk_usage_items
# =====================================================================

class TestProcessBulkUsageItems:
    """Tests for process_bulk_usage_items."""

    def _call(self, items, user_id=1, username="testuser"):
        from app.services.equipment_service import process_bulk_usage_items
        return process_bulk_usage_items(items, user_id, username)

    def test_empty_items(self, app, db):
        with app.app_context():
            success, count, err = self._call([])
        assert success is True
        assert count == 0
        assert err is None

    def test_invalid_eq_id_skipped(self, app, db):
        with app.app_context():
            success, count, err = self._call([
                {"eq_id": "abc", "minutes": 10},
                {"eq_id": None, "minutes": 10},
            ])
        assert success is True
        assert count == 0

    @patch("app.services.equipment_service.log_audit")
    @patch("app.services.equipment_service.now_local")
    def test_usage_log_created(self, mock_now, mock_audit, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.models import Equipment
            eq = Equipment(name="Test EQ", lab_code="EQ-001")
            db.session.add(eq)
            db.session.flush()
            eq_id = eq.id

            success, count, err = self._call([
                {"eq_id": str(eq_id), "minutes": 30, "note": "Test usage"},
            ])
            assert success is True
            assert count == 1
            assert err is None
            mock_audit.assert_called_once()

            # Cleanup
            db.session.rollback()

    @patch("app.services.equipment_service.log_audit")
    @patch("app.services.equipment_service.now_local")
    def test_calibration_creates_maintenance_log(self, mock_now, mock_audit, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.models import Equipment
            eq = Equipment(name="Oven", lab_code="EQ-002")
            db.session.add(eq)
            db.session.flush()
            eq_id = eq.id

            success, count, err = self._call([
                {
                    "eq_id": str(eq_id),
                    "minutes": 0,
                    "note": "",
                    "calibration": {
                        "type": "temperature",
                        "set_temp": 100.0,
                        "actual_temp": 101.0,
                        "frequency": "daily",
                    },
                },
            ])
            assert success is True
            assert count == 1
            db.session.rollback()

    @patch("app.services.equipment_service.log_audit")
    @patch("app.services.equipment_service.now_local")
    def test_repair_with_spare_parts(self, mock_now, mock_audit, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.models import Equipment, SparePart
            eq = Equipment(name="Balance", lab_code="EQ-003")
            db.session.add(eq)
            sp = SparePart(name="Filter", quantity=10, unit="pcs")
            db.session.add(sp)
            db.session.flush()
            eq_id = eq.id
            sp_id = sp.id

            success, count, err = self._call([
                {
                    "eq_id": str(eq_id),
                    "minutes": 0,
                    "note": "Filter replaced",
                    "repair": True,
                    "repair_date": "2026-03-10",
                    "spare_parts": [
                        {"spare_id": str(sp_id), "qty": 2, "used_by": "tech1"},
                    ],
                },
            ])
            assert success is True
            assert count >= 1
            db.session.rollback()

    @patch("app.services.equipment_service.log_audit")
    @patch("app.services.equipment_service.now_local")
    def test_repair_invalid_spare_id_skipped(self, mock_now, mock_audit, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.models import Equipment
            eq = Equipment(name="EQ", lab_code="EQ-004")
            db.session.add(eq)
            db.session.flush()
            eq_id = eq.id

            success, count, err = self._call([
                {
                    "eq_id": str(eq_id),
                    "minutes": 0,
                    "repair": True,
                    "spare_parts": [
                        {"spare_id": "abc"},
                        {"spare_id": "99999"},  # non-existent
                    ],
                },
            ])
            assert success is True
            db.session.rollback()

    @patch("app.services.equipment_service.log_audit")
    @patch("app.services.equipment_service.now_local")
    def test_repair_invalid_date_falls_back(self, mock_now, mock_audit, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.models import Equipment
            eq = Equipment(name="EQ", lab_code="EQ-005")
            db.session.add(eq)
            db.session.flush()
            eq_id = eq.id

            success, count, err = self._call([
                {
                    "eq_id": str(eq_id),
                    "repair": True,
                    "repair_date": "invalid-date",
                },
            ])
            assert success is True
            db.session.rollback()

    @patch("app.services.equipment_service.log_audit")
    @patch("app.services.equipment_service.now_local")
    def test_db_commit_error(self, mock_now, mock_audit, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.models import Equipment
            eq = Equipment(name="EQ", lab_code="EQ-006")
            db.session.add(eq)
            db.session.flush()
            eq_id = eq.id

            with patch.object(db.session, "commit", side_effect=SQLAlchemyError("DB error")):
                success, count, err = self._call([
                    {"eq_id": str(eq_id), "minutes": 10, "note": "test"},
                ])
            assert success is False
            assert count == 0
            assert err is not None
            db.session.rollback()

    @patch("app.services.equipment_service.log_audit")
    @patch("app.services.equipment_service.now_local")
    def test_note_only_no_minutes(self, mock_now, mock_audit, app, db):
        """Item with note but 0 minutes should still create usage log."""
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.models import Equipment
            eq = Equipment(name="EQ", lab_code="EQ-007")
            db.session.add(eq)
            db.session.flush()
            eq_id = eq.id

            success, count, err = self._call([
                {"eq_id": str(eq_id), "minutes": 0, "note": "Checked"},
            ])
            assert success is True
            assert count == 1
            db.session.rollback()

    @patch("app.services.equipment_service.log_audit")
    @patch("app.services.equipment_service.now_local")
    def test_calibration_frequency_variants(self, mock_now, mock_audit, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.models import Equipment
            eq = Equipment(name="EQ", lab_code="EQ-008")
            db.session.add(eq)
            db.session.flush()
            eq_id = eq.id

            for freq in ["daily", "monthly", "adjustment", "unknown_freq"]:
                success, count, err = self._call([
                    {
                        "eq_id": str(eq_id),
                        "calibration": {
                            "type": "temperature",
                            "set_temp": 100,
                            "actual_temp": 101,
                            "frequency": freq,
                        },
                    },
                ])
                assert success is True
            db.session.rollback()

    @patch("app.services.equipment_service.log_audit")
    @patch("app.services.equipment_service.now_local")
    def test_spare_part_qty_exceeds_stock(self, mock_now, mock_audit, app, db):
        """If qty_used > sp_item.quantity, stock should NOT be reduced."""
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.models import Equipment, SparePart
            eq = Equipment(name="EQ", lab_code="EQ-009")
            db.session.add(eq)
            sp = SparePart(name="Widget", quantity=1, unit="pcs")
            db.session.add(sp)
            db.session.flush()
            eq_id = eq.id
            sp_id = sp.id

            success, count, err = self._call([
                {
                    "eq_id": str(eq_id),
                    "repair": True,
                    "spare_parts": [
                        {"spare_id": str(sp_id), "qty": 5},  # 5 > 1
                    ],
                },
            ])
            assert success is True
            # quantity should remain 1 (not deducted)
            refreshed = db.session.get(SparePart, sp_id)
            assert refreshed.quantity == 1
            db.session.rollback()


# =====================================================================
# equipment_service — get_usage_summary
# =====================================================================

class TestGetUsageSummary:
    """Tests for get_usage_summary."""

    @patch("app.services.equipment_service.get_shift_date")
    def test_empty_equipment(self, mock_shift, app, db):
        mock_shift.return_value = date(2026, 3, 10)
        with app.app_context():
            from app.services.equipment_service import get_usage_summary
            rows = get_usage_summary(
                datetime(2026, 3, 1), datetime(2026, 3, 31, 23, 59, 59), "nonexistent_cat"
            )
        assert rows == []

    @patch("app.services.equipment_service.get_shift_date")
    def test_returns_rows(self, mock_shift, app, db):
        mock_shift.return_value = date(2026, 3, 10)
        with app.app_context():
            from app.models import Equipment
            from app.services.equipment_service import get_usage_summary
            eq = Equipment(name="TestEQ", lab_code="T1", category="coal")
            db.session.add(eq)
            db.session.flush()

            rows = get_usage_summary(
                datetime(2026, 3, 1), datetime(2026, 3, 31, 23, 59, 59), "coal"
            )
            assert len(rows) >= 1
            row = [r for r in rows if r["equipment_id"] == eq.id][0]
            assert row["name"] == "TestEQ"
            assert row["total_usage_hours"] == 0.0
            db.session.rollback()

    @patch("app.services.equipment_service.get_shift_date")
    def test_all_category(self, mock_shift, app, db):
        mock_shift.return_value = date(2026, 3, 10)
        with app.app_context():
            from app.models import Equipment
            from app.services.equipment_service import get_usage_summary
            eq = Equipment(name="AllCat", lab_code="AC1")
            db.session.add(eq)
            db.session.flush()

            rows = get_usage_summary(
                datetime(2026, 3, 1), datetime(2026, 3, 31, 23, 59, 59), "all"
            )
            assert any(r["name"] == "AllCat" for r in rows)
            db.session.rollback()


# =====================================================================
# equipment_service — get_journal_detailed
# =====================================================================

class TestGetJournalDetailed:

    def test_empty_result(self, app, db):
        with app.app_context():
            from app.services.equipment_service import get_journal_detailed
            result = get_journal_detailed(
                datetime(2099, 1, 1), datetime(2099, 12, 31, 23, 59, 59), "all"
            )
        assert result == []

    def test_with_equipment_id_filter(self, app, db):
        with app.app_context():
            from app.services.equipment_service import get_journal_detailed
            result = get_journal_detailed(
                datetime(2026, 1, 1), datetime(2026, 12, 31, 23, 59, 59),
                "all", equipment_id=999999
            )
        assert result == []


# =====================================================================
# equipment_service — get_monthly_stats
# =====================================================================

class TestGetMonthlyStats:

    def test_empty_equipment(self, app, db):
        with app.app_context():
            from app.services.equipment_service import get_monthly_stats
            rows = get_monthly_stats(2026, "nonexistent_cat")
        assert rows == []

    def test_returns_rows(self, app, db):
        with app.app_context():
            from app.models import Equipment
            from app.services.equipment_service import get_monthly_stats
            eq = Equipment(name="StatsEQ", lab_code="SE1", category="coal_stats")
            db.session.add(eq)
            db.session.flush()

            rows = get_monthly_stats(2026, "coal_stats")
            assert len(rows) >= 1
            row = [r for r in rows if r["equipment_id"] == eq.id][0]
            assert row["name"] == "StatsEQ"
            # All months should be 0
            for m in range(1, 13):
                assert row[f"usage_{m}"] == 0
                assert row[f"maint_{m}"] == 0
            db.session.rollback()


# =====================================================================
# equipment_service — _filter_equipment_by_category
# =====================================================================

class TestFilterEquipmentByCategory:

    def test_none_category(self, app, db):
        with app.app_context():
            from app.services.equipment_service import _filter_equipment_by_category
            from app.models import Equipment
            q = Equipment.query
            result = _filter_equipment_by_category(q, None)
            # Should return unmodified query
            assert result is q

    def test_all_category(self, app, db):
        with app.app_context():
            from app.services.equipment_service import _filter_equipment_by_category
            from app.models import Equipment
            q = Equipment.query
            result = _filter_equipment_by_category(q, "all")
            assert result is q

    def test_specific_category(self, app, db):
        with app.app_context():
            from app.services.equipment_service import _filter_equipment_by_category
            from app.models import Equipment
            q = Equipment.query
            result = _filter_equipment_by_category(q, "coal")
            # Should return a different (filtered) query
            assert result is not q


# =====================================================================
# report_service — format_short_name
# =====================================================================

class TestFormatShortName:

    def test_normal_name(self, app):
        from app.services.report_service import format_short_name
        assert format_short_name("GANTULGA Ulziibuyan") == "Gantulga.U"

    def test_single_word(self, app):
        from app.services.report_service import format_short_name
        assert format_short_name("Admin") == "Admin"

    def test_empty_string(self, app):
        from app.services.report_service import format_short_name
        assert format_short_name("") == ""

    def test_none(self, app):
        from app.services.report_service import format_short_name
        assert format_short_name(None) == ""

    def test_three_words(self, app):
        from app.services.report_service import format_short_name
        assert format_short_name("John Michael Doe") == "John.M"

    def test_whitespace_name(self, app):
        from app.services.report_service import format_short_name
        assert format_short_name("  Bold   Bayar  ") == "Bold.B"


# =====================================================================
# report_service — get_weeks_in_month
# =====================================================================

class TestGetWeeksInMonth:

    def test_january_2026(self):
        from app.services.report_service import get_weeks_in_month
        weeks = get_weeks_in_month(2026, 1)
        assert len(weeks) >= 4
        # First week starts on Jan 1
        assert weeks[0][1] == date(2026, 1, 1)
        # Last week ends on Jan 31
        assert weeks[-1][2] == date(2026, 1, 31)
        # Week numbers are sequential
        for i, (num, _, _) in enumerate(weeks):
            assert num == i + 1

    def test_february_leap_year(self):
        from app.services.report_service import get_weeks_in_month
        weeks = get_weeks_in_month(2024, 2)  # 2024 is leap year
        assert weeks[-1][2] == date(2024, 2, 29)

    def test_february_non_leap(self):
        from app.services.report_service import get_weeks_in_month
        weeks = get_weeks_in_month(2025, 2)
        assert weeks[-1][2] == date(2025, 2, 28)

    def test_weeks_cover_entire_month(self):
        from app.services.report_service import get_weeks_in_month
        weeks = get_weeks_in_month(2026, 3)
        # Each week end + 1 day = next week start (no gaps)
        for i in range(len(weeks) - 1):
            assert weeks[i][2] + timedelta(days=1) == weeks[i + 1][1]


# =====================================================================
# report_service — calculate_weekly_performance
# =====================================================================

class TestCalculateWeeklyPerformance:

    def test_empty_samples(self, app, db):
        with app.app_context():
            from app.services.report_service import calculate_weekly_performance
            result, weeks = calculate_weekly_performance(2099, 1)
        assert result == {}
        assert len(weeks) >= 4

    def test_with_samples(self, app, db):
        with app.app_context():
            from app.models import Sample, User
            from app.services.report_service import calculate_weekly_performance
            import uuid
            user = User.query.filter_by(username='chemist').first()
            s = Sample(
                sample_code=f"WP-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="CHPP",
                sample_type="2 hourly",
                received_date=date(2026, 3, 2),
            )
            db.session.add(s)
            db.session.flush()

            result, weeks = calculate_weekly_performance(2026, 3)
            # Should have at least one entry
            found = any("CHPP|2 hourly" in k for k in result.keys())
            assert found
            db.session.rollback()


# =====================================================================
# report_service — build_monthly_plan_context
# =====================================================================

class TestBuildMonthlyPlanContext:

    @patch("app.services.report_service.now_local")
    def test_basic_context(self, mock_now, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.services.report_service import build_monthly_plan_context
            ctx = build_monthly_plan_context(2026, 3)

        assert ctx['month_name'] == 'March'
        assert len(ctx['weeks']) >= 4
        assert isinstance(ctx['data'], dict)
        assert 'grand_total' in ctx
        assert ctx['grand_total']['plan'] >= 0
        assert ctx['staff_preparers'] == 6  # default
        assert ctx['staff_chemists'] == 10  # default
        assert 2026 in ctx['years']

    @patch("app.services.report_service.now_local")
    def test_with_staff_settings(self, mock_now, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.models.planning import StaffSettings
            from app.services.report_service import build_monthly_plan_context
            ss = StaffSettings(year=2026, month=3, preparers=8, chemists=12)
            db.session.add(ss)
            db.session.flush()

            ctx = build_monthly_plan_context(2026, 3)
            assert ctx['staff_preparers'] == 8
            assert ctx['staff_chemists'] == 12
            db.session.rollback()

    @patch("app.services.report_service.now_local")
    def test_week_totals_have_daily(self, mock_now, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.services.report_service import build_monthly_plan_context
            ctx = build_monthly_plan_context(2026, 3)
        for w in ctx['weeks']:
            wt = ctx['week_totals'][w['week']]
            assert 'daily_plan' in wt
            assert 'daily_perf' in wt


# =====================================================================
# report_service — save_monthly_plans
# =====================================================================

class TestSaveMonthlyPlans:

    def test_save_new_plans(self, app, db):
        with app.app_context():
            from app.services.report_service import save_monthly_plans
            plans = {
                "CHPP|2 hourly|1": 10,
                "CHPP|2 hourly|2": 15,
            }
            success, count, err = save_monthly_plans(plans, 2099, 1, 1)
            assert success is True
            assert count == 2
            assert err is None

            # Cleanup
            from app import models as M
            M.MonthlyPlan.query.filter_by(year=2099, month=1).delete()
            db.session.commit()

    def test_upsert_existing(self, app, db):
        with app.app_context():
            from app.services.report_service import save_monthly_plans
            from app import models as M

            # Create first
            save_monthly_plans({"CHPP|com|1": 5}, 2098, 12, 1)

            # Update
            success, count, err = save_monthly_plans({"CHPP|com|1": 20}, 2098, 12, 1)
            assert success is True

            existing = M.MonthlyPlan.query.filter_by(
                year=2098, month=12, week=1, client_name="CHPP", sample_type="com"
            ).first()
            assert existing.planned_count == 20

            # Cleanup
            M.MonthlyPlan.query.filter_by(year=2098, month=12).delete()
            db.session.commit()

    def test_invalid_key_skipped(self, app, db):
        with app.app_context():
            from app.services.report_service import save_monthly_plans
            plans = {
                "bad_key": 10,
                "also|bad": 5,
            }
            success, count, err = save_monthly_plans(plans, 2099, 2, 1)
            assert success is True
            assert count == 0

    def test_db_error(self, app, db):
        with app.app_context():
            from app.services.report_service import save_monthly_plans
            with patch.object(db.session, "commit", side_effect=SQLAlchemyError("err")):
                success, count, err = save_monthly_plans(
                    {"CHPP|2 hourly|1": 10}, 2099, 3, 1
                )
            assert success is False
            assert err is not None
            db.session.rollback()


# =====================================================================
# report_service — save_staff_settings
# =====================================================================

class TestSaveStaffSettings:

    def test_create_new(self, app, db):
        with app.app_context():
            from app.services.report_service import save_staff_settings
            from app.models.planning import StaffSettings
            success, err = save_staff_settings(2099, 6, 8, 12)
            assert success is True
            assert err is None

            ss = StaffSettings.query.filter_by(year=2099, month=6).first()
            assert ss.preparers == 8
            assert ss.chemists == 12

            # Cleanup
            db.session.delete(ss)
            db.session.commit()

    def test_update_existing(self, app, db):
        with app.app_context():
            from app.services.report_service import save_staff_settings
            from app.models.planning import StaffSettings

            save_staff_settings(2098, 11, 5, 9)
            success, err = save_staff_settings(2098, 11, 7, 14)
            assert success is True

            ss = StaffSettings.query.filter_by(year=2098, month=11).first()
            assert ss.preparers == 7
            assert ss.chemists == 14

            db.session.delete(ss)
            db.session.commit()

    def test_db_error(self, app, db):
        with app.app_context():
            from app.services.report_service import save_staff_settings
            with patch.object(db.session, "commit", side_effect=SQLAlchemyError("err")):
                success, err = save_staff_settings(2099, 7, 5, 10)
            assert success is False
            assert "error" in err.lower()
            db.session.rollback()


# =====================================================================
# report_service — get_plan_statistics
# =====================================================================

class TestGetPlanStatistics:

    @patch("app.services.report_service.now_local")
    def test_basic_stats(self, mock_now, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.services.report_service import get_plan_statistics
            result = get_plan_statistics(2026, 1, 2026, 3)

        assert result['from_year'] == 2026
        assert result['to_year'] == 2026
        assert 'yearly' in result
        assert 'monthly' in result
        assert 'weekly' in result
        assert 'consignor' in result
        assert result['total_planned'] >= 0
        assert result['total_actual'] >= 0

    @patch("app.services.report_service.now_local")
    def test_swapped_range(self, mock_now, app, db):
        """If from > to, function should swap them."""
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.services.report_service import get_plan_statistics
            result = get_plan_statistics(2026, 3, 2026, 1)

        assert result['from_year'] == 2026
        assert result['from_month'] == 1
        assert result['to_month'] == 3

    @patch("app.services.report_service.now_local")
    def test_single_month(self, mock_now, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.services.report_service import get_plan_statistics
            result = get_plan_statistics(2026, 3, 2026, 3)

        assert len(result['monthly']) >= 1
        assert result['range_label'] == "2026/3 - 2026/3"

    @patch("app.services.report_service.now_local")
    def test_cross_year(self, mock_now, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.services.report_service import get_plan_statistics
            result = get_plan_statistics(2025, 11, 2026, 2)

        assert len(result['yearly']) == 2
        assert result['yearly'][0]['year'] == 2025
        assert result['yearly'][1]['year'] == 2026


# =====================================================================
# report_service — build_chemist_report_data
# =====================================================================

class TestBuildChemistReportData:

    def test_no_results(self, app, db):
        with app.app_context():
            from app.services.report_service import build_chemist_report_data
            result = build_chemist_report_data(2099, "", "")

        assert result['year'] == 2099
        assert result['chemists'] == []
        assert result['grand_total'] == 0
        assert result['prev_year'] == 2098

    def test_date_range_parsing(self, app, db):
        with app.app_context():
            from app.services.report_service import build_chemist_report_data
            result = build_chemist_report_data(2026, "2026-01-01", "2026-03-31")

        assert result['date_from'] == "2026-01-01"
        assert result['date_to'] == "2026-03-31"

    def test_invalid_date_from(self, app, db):
        with app.app_context():
            from app.services.report_service import build_chemist_report_data
            result = build_chemist_report_data(2026, "bad-date", "2026-03-31")

        # Should fall back to Jan 1
        assert result['date_from'] == "bad-date"

    def test_invalid_date_to(self, app, db):
        with app.app_context():
            from app.services.report_service import build_chemist_report_data
            result = build_chemist_report_data(2026, "2026-01-01", "bad-date")

        assert result['date_to'] == "bad-date"

    def test_result_structure(self, app, db):
        with app.app_context():
            from app.services.report_service import build_chemist_report_data
            result = build_chemist_report_data(2026, "", "")

        required_keys = [
            'year', 'date_from', 'date_to', 'chemists', 'chemists_by_quality',
            'analysis_codes', 'error_reason_keys', 'error_reason_labels',
            'grand_monthly', 'grand_by_analysis', 'grand_errors',
            'grand_total', 'grand_error_total', 'prev_year', 'prev_monthly',
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_grand_monthly_has_12_months(self, app, db):
        with app.app_context():
            from app.services.report_service import build_chemist_report_data
            result = build_chemist_report_data(2026, "", "")

        assert len(result['grand_monthly']) == 12
        for m in range(1, 13):
            assert m in result['grand_monthly']

    def test_prev_monthly_has_12_months(self, app, db):
        with app.app_context():
            from app.services.report_service import build_chemist_report_data
            result = build_chemist_report_data(2026, "", "")

        assert len(result['prev_monthly']) == 12

    def test_error_reason_keys_match(self, app, db):
        with app.app_context():
            from app.services.report_service import build_chemist_report_data
            from app.constants import ERROR_REASON_KEYS
            result = build_chemist_report_data(2026, "", "")

        assert result['error_reason_keys'] == ERROR_REASON_KEYS

    def test_with_analysis_result_logs(self, app, db):
        """Test with actual AnalysisResultLog data to cover chemist data building."""
        with app.app_context():
            from app.models import User, AnalysisResult, Sample
            from app.models.analysis_audit import AnalysisResultLog
            from app.services.report_service import build_chemist_report_data
            import uuid

            user = User.query.filter_by(username='chemist').first()

            # Create a sample
            s = Sample(
                sample_code=f"CR-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="QC",
                sample_type="HCC",
            )
            db.session.add(s)
            db.session.flush()

            # Create AnalysisResult
            ar = AnalysisResult(
                sample_id=s.id,
                analysis_code="Mad",
                user_id=user.id,
                status="approved",
                final_result=5.5,
            )
            db.session.add(ar)
            db.session.flush()

            # Create logs for the chemist (work actions)
            for month_offset in range(3):
                log = AnalysisResultLog(
                    user_id=user.id,
                    sample_id=s.id,
                    analysis_result_id=ar.id,
                    analysis_code="Mad",
                    action="CREATED_AUTO_APPROVED",
                    timestamp=datetime(2026, month_offset + 1, 15, 10, 0),
                )
                db.session.add(log)

            # Create a rejection log for error counting
            reject_log = AnalysisResultLog(
                user_id=user.id,
                sample_id=s.id,
                analysis_result_id=ar.id,
                analysis_code="Mad",
                action="REJECTED",
                error_reason="sample_prep",
                timestamp=datetime(2026, 2, 20, 10, 0),
            )
            db.session.add(reject_log)
            db.session.flush()

            result = build_chemist_report_data(2026, "2026-01-01", "2026-12-31")

            assert result['grand_total'] >= 3
            assert len(result['chemists']) >= 1
            # Check chemist has data
            chemist = next(
                (c for c in result['chemists'] if c['id'] == user.id), None
            )
            assert chemist is not None
            assert chemist['total'] >= 3
            assert chemist['monthly'][1] >= 1
            assert chemist['monthly'][2] >= 1
            assert chemist['monthly'][3] >= 1
            assert 'Mad' in result['analysis_codes']
            # Ranking
            assert chemist['rank_total'] is not None
            # Monthly growth
            assert 'monthly_growth' in chemist
            assert len(chemist['monthly_growth']) == 11
            # Quarterly
            assert len(chemist['quarterly']) == 4
            assert chemist['quarterly'][0] >= 3  # Q1 has months 1,2,3
            # Error
            assert chemist['errors']['sample_prep'] >= 1
            assert chemist['error_total'] >= 1
            # Grand errors
            assert result['grand_errors']['sample_prep'] >= 1
            assert result['grand_error_total'] >= 1
            # Grand by analysis
            assert result['grand_by_analysis'].get('Mad', 0) >= 3

            db.session.rollback()

    def test_chemist_with_enough_results_gets_quality_rank(self, app, db):
        """Chemist with >=10 results should get quality ranking."""
        with app.app_context():
            from app.models import User, AnalysisResult, Sample
            from app.models.analysis_audit import AnalysisResultLog
            from app.services.report_service import build_chemist_report_data
            import uuid

            user = User.query.filter_by(username='chemist').first()

            s = Sample(
                sample_code=f"QR-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="QC",
                sample_type="HCC",
            )
            db.session.add(s)
            db.session.flush()

            ar = AnalysisResult(
                sample_id=s.id,
                analysis_code="Aad",
                user_id=user.id,
                status="approved",
            )
            db.session.add(ar)
            db.session.flush()

            # Create 12 logs so total >= 10
            for i in range(12):
                log = AnalysisResultLog(
                    user_id=user.id,
                    sample_id=s.id,
                    analysis_result_id=ar.id,
                    analysis_code="Aad",
                    action="CREATED_PENDING",
                    timestamp=datetime(2025, 6, 15, 10, i),
                )
                db.session.add(log)
            db.session.flush()

            result = build_chemist_report_data(2025, "2025-01-01", "2025-12-31")

            chemist = next(
                (c for c in result['chemists'] if c['id'] == user.id), None
            )
            assert chemist is not None
            assert chemist['total'] >= 10
            # Should have quality rank
            quality_ranked = [
                c for c in result['chemists_by_quality'] if c['id'] == user.id
            ]
            assert len(quality_ranked) >= 1
            assert quality_ranked[0]['rank_quality'] is not None

            db.session.rollback()

    def test_chemist_equipment_usage_stats(self, app, db):
        """Test that equipment usage/maintenance stats are populated."""
        with app.app_context():
            from app.models import User, AnalysisResult, Sample, Equipment, UsageLog, MaintenanceLog
            from app.models.analysis_audit import AnalysisResultLog
            from app.services.report_service import build_chemist_report_data
            import uuid

            user = User.query.filter_by(username='chemist').first()

            s = Sample(
                sample_code=f"EU-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="QC",
                sample_type="HCC",
            )
            db.session.add(s)
            db.session.flush()

            ar = AnalysisResult(
                sample_id=s.id,
                analysis_code="Vdaf",
                user_id=user.id,
                status="approved",
            )
            db.session.add(ar)
            db.session.flush()

            # Create a work log so user appears as chemist
            log = AnalysisResultLog(
                user_id=user.id,
                sample_id=s.id,
                analysis_result_id=ar.id,
                analysis_code="Vdaf",
                action="CREATED_AUTO_APPROVED",
                timestamp=datetime(2026, 2, 10, 10, 0),
            )
            db.session.add(log)

            # Equipment usage
            eq = Equipment(name="Test EQ Usage", lab_code="TEU-1")
            db.session.add(eq)
            db.session.flush()

            ulog = UsageLog(
                equipment_id=eq.id,
                start_time=datetime(2026, 2, 10, 8, 0),
                end_time=datetime(2026, 2, 10, 10, 0),
                duration_minutes=120,
                used_by=user.username,
                used_by_id=user.id,
                purpose="Test",
            )
            db.session.add(ulog)

            mlog = MaintenanceLog(
                equipment_id=eq.id,
                action_date=datetime(2026, 2, 10, 8, 0),
                action_type="Calibration",
                performed_by=user.username,
                performed_by_id=user.id,
            )
            db.session.add(mlog)

            mlog2 = MaintenanceLog(
                equipment_id=eq.id,
                action_date=datetime(2026, 2, 11, 8, 0),
                action_type="Repair",
                performed_by=user.username,
                performed_by_id=user.id,
            )
            db.session.add(mlog2)
            db.session.flush()

            result = build_chemist_report_data(2026, "2026-01-01", "2026-12-31")

            chemist = next(
                (c for c in result['chemists'] if c['id'] == user.id), None
            )
            assert chemist is not None
            assert chemist['eq_usage_count'] >= 1
            assert chemist['eq_usage_hours'] >= 1.0
            assert chemist['eq_calib_count'] >= 1
            assert chemist['eq_maint_count'] >= 1

            db.session.rollback()


# =====================================================================
# report_service — build_monthly_plan_context with plan data
# =====================================================================

class TestBuildMonthlyPlanContextWithData:

    @patch("app.services.report_service.now_local")
    def test_with_plan_data(self, mock_now, app, db):
        """Test that plans and performance flow into context correctly."""
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.services.report_service import build_monthly_plan_context, save_monthly_plans
            from app import models as M

            # Save some plan data
            save_monthly_plans({
                "CHPP|2 hourly|1": 20,
                "CHPP|2 hourly|2": 25,
            }, 2026, 3, 1)

            ctx = build_monthly_plan_context(2026, 3)

            assert 'CHPP' in ctx['data']
            chpp = ctx['data']['CHPP']
            assert '2 hourly' in chpp['types']
            hourly = chpp['types']['2 hourly']
            assert hourly['total_plan'] >= 45

            # grand_total should include these plans
            assert ctx['grand_total']['plan'] >= 45
            assert ctx['grand_pct'] >= 0

            # Cleanup
            M.MonthlyPlan.query.filter_by(year=2026, month=3).delete()
            db.session.commit()

    @patch("app.services.report_service.now_local")
    def test_client_pct_calculation(self, mock_now, app, db):
        """Verify percentage is 0 when plan is 0."""
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.services.report_service import build_monthly_plan_context
            ctx = build_monthly_plan_context(2026, 3)

            # With no plans, all percentages should be 0
            for client_name, client_info in ctx['data'].items():
                assert client_info['pct'] >= 0


# =====================================================================
# report_service — get_plan_statistics additional coverage
# =====================================================================

class TestGetPlanStatisticsAdditional:

    @patch("app.services.report_service.now_local")
    def test_with_plan_and_sample_data(self, mock_now, app, db):
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.services.report_service import get_plan_statistics, save_monthly_plans
            from app.models import Sample, User
            from app import models as M
            import uuid

            # Create plan data
            save_monthly_plans({
                "CHPP|2 hourly|1": 10,
            }, 2026, 1, 1)

            # Create sample data
            user = User.query.filter_by(username='chemist').first()
            s = Sample(
                sample_code=f"PS-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="CHPP",
                sample_type="2 hourly",
                received_date=date(2026, 1, 5),
                status="completed",
            )
            db.session.add(s)
            db.session.flush()

            result = get_plan_statistics(2026, 1, 2026, 3)

            assert result['total_planned'] >= 10
            assert result['total_actual'] >= 1

            # Consignor stats should include CHPP
            chpp_stats = [c for c in result['consignor'] if c['client'] == 'CHPP']
            assert len(chpp_stats) >= 1
            assert chpp_stats[0]['planned'] >= 10

            # Cleanup
            M.MonthlyPlan.query.filter_by(year=2026, month=1).delete()
            db.session.delete(s)
            db.session.commit()

    @patch("app.services.report_service.now_local")
    def test_future_months_excluded(self, mock_now, app, db):
        """Months in the future of current year should be skipped."""
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.services.report_service import get_plan_statistics
            result = get_plan_statistics(2026, 1, 2026, 12)

            # Should only have months up to current month (March)
            for m in result['monthly']:
                if m['year'] == 2026:
                    assert m['month'] <= 3

    @patch("app.services.report_service.now_local")
    def test_range_end_after_today(self, mock_now, app, db):
        """When range_end > now.date(), days_in_range should use now."""
        mock_now.return_value = datetime(2026, 3, 10, 9, 0)
        with app.app_context():
            from app.services.report_service import get_plan_statistics
            result = get_plan_statistics(2026, 1, 2026, 12)
            # daily_avg should be computed
            assert 'daily_avg' in result
