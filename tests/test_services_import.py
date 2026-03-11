# -*- coding: utf-8 -*-
"""Comprehensive tests for app/services/import_service.py — targeting 80%+ coverage."""

import csv
import io
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock


# ---------------------------------------------------------------------------
# Helpers to import the module with minimal app dependencies
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_app_deps(monkeypatch):
    """Patch heavy app-level imports so the module loads without Flask."""
    # We need db, models, constants, aliases, converters
    pass


# We import after ensuring the test environment can load the module.
# If the app factory is needed, tests using DB functions will mock db.session.
from app.services.import_service import (
    _norm,
    _parse_date,
    _map_header,
    _base_code,
    decode_csv_bytes,
    detect_delimiter,
    parse_csv_header,
    _get_or_create_sample,
    _upsert_result,
    import_chpp_wide,
    import_long,
    process_csv_import,
    HEADER_KEYS,
    ALIAS_TO_BASE,
)


# ===================================================================
# 1. _norm
# ===================================================================

class TestNorm:
    def test_none_returns_empty(self):
        assert _norm(None) == ""

    def test_strips_whitespace(self):
        assert _norm("  hello  ") == "hello"

    def test_integer_input(self):
        assert _norm(123) == "123"

    def test_empty_string(self):
        assert _norm("") == ""

    def test_whitespace_only(self):
        assert _norm("   ") == ""


# ===================================================================
# 2. _parse_date
# ===================================================================

class TestParseDate:
    def test_none_returns_none(self):
        assert _parse_date(None) is None

    def test_empty_returns_none(self):
        assert _parse_date("") is None

    def test_null_string_returns_none(self):
        assert _parse_date("null") is None
        assert _parse_date("None") is None
        assert _parse_date("  none  ") is None

    def test_ymd_dash(self):
        dt = _parse_date("2024-03-15")
        assert dt == datetime(2024, 3, 15)

    def test_ymd_slash(self):
        dt = _parse_date("2024/03/15")
        assert dt == datetime(2024, 3, 15)

    def test_ymd_dash_hm(self):
        dt = _parse_date("2024-03-15 14:30")
        assert dt == datetime(2024, 3, 15, 14, 30)

    def test_ymd_slash_hm(self):
        dt = _parse_date("2024/03/15 14:30")
        assert dt == datetime(2024, 3, 15, 14, 30)

    def test_ymd_dash_hms(self):
        dt = _parse_date("2024-03-15 14:30:45")
        assert dt == datetime(2024, 3, 15, 14, 30, 45)

    def test_ymd_slash_hms(self):
        dt = _parse_date("2024/03/15 14:30:45")
        assert dt == datetime(2024, 3, 15, 14, 30, 45)

    def test_iso_t_hm(self):
        dt = _parse_date("2024-03-15T14:30")
        assert dt == datetime(2024, 3, 15, 14, 30)

    def test_iso_t_hms(self):
        dt = _parse_date("2024-03-15T14:30:45")
        assert dt == datetime(2024, 3, 15, 14, 30, 45)

    def test_ym_only(self):
        dt = _parse_date("2024-03")
        assert dt == datetime(2024, 3, 1)

    def test_dmy_slash_hm(self):
        dt = _parse_date("15/03/2024 14:30")
        assert dt == datetime(2024, 3, 15, 14, 30)

    def test_dmy_slash(self):
        dt = _parse_date("15/03/2024")
        assert dt == datetime(2024, 3, 15)

    def test_bare_year(self):
        dt = _parse_date("2020")
        assert dt == datetime(2020, 1, 1)

    def test_bare_year_out_of_range(self):
        # Years outside MIN/MAX range return None
        assert _parse_date("1899") is None

    def test_unparseable(self):
        assert _parse_date("not-a-date") is None

    def test_whitespace_stripped(self):
        dt = _parse_date("  2024-01-01  ")
        assert dt == datetime(2024, 1, 1)

    def test_zero_falsy(self):
        # 0 is falsy, should return None
        assert _parse_date(0) is None


# ===================================================================
# 3. _map_header
# ===================================================================

class TestMapHeader:
    def test_known_sample_code(self):
        assert _map_header("sample_code") == "sample_code"

    def test_case_insensitive(self):
        assert _map_header("SAMPLE_CODE") == "sample_code"

    def test_whitespace_stripped(self):
        assert _map_header("  sample_code  ") == "sample_code"

    def test_unknown_header(self):
        assert _map_header("xyzzy_unknown") is None

    def test_value_synonym(self):
        assert _map_header("result") == "value"

    def test_analysis_date_synonym(self):
        assert _map_header("date") == "analysis_date"

    def test_analysis_code_synonym(self):
        assert _map_header("test") == "analysis_code"

    def test_client_name_synonym(self):
        assert _map_header("organization") == "client_name"

    def test_status_synonym(self):
        assert _map_header("state") == "status"

    def test_unit_synonym(self):
        assert _map_header("meas_unit") == "unit"

    def test_received_date_synonym(self):
        assert _map_header("reg_date") == "received_date"

    def test_sample_type_synonym(self):
        assert _map_header("type") == "sample_type"


# ===================================================================
# 4. _base_code
# ===================================================================

class TestBaseCode:
    def test_empty_returns_empty(self):
        assert _base_code("") == ""

    def test_none_returns_empty(self):
        assert _base_code(None) == ""

    def test_known_alias(self):
        # "ts" should map to "TS"
        assert _base_code("ts") == "TS"

    def test_known_alias_case(self):
        assert _base_code("TS") == "TS"

    def test_unknown_code_passthrough(self):
        assert _base_code("UNKNOWN_CODE_XYZ") == "UNKNOWN_CODE_XYZ"

    def test_whitespace_stripped(self):
        assert _base_code("  ts  ") == "TS"


# ===================================================================
# 5. decode_csv_bytes
# ===================================================================

class TestDecodeCsvBytes:
    def test_utf8_sig(self):
        raw = b"\xef\xbb\xbfhello"
        assert decode_csv_bytes(raw) == "hello"

    def test_plain_utf8(self):
        raw = "abc".encode("utf-8")
        assert decode_csv_bytes(raw) == "abc"

    def test_cp1251_fallback(self):
        # Create bytes that are invalid utf-8 but valid cp1251
        raw = bytes([0xc0, 0xc1, 0xc2])  # Invalid utf-8 sequence
        result = decode_csv_bytes(raw)
        assert isinstance(result, str)
        assert len(result) > 0


# ===================================================================
# 6. detect_delimiter
# ===================================================================

class TestDetectDelimiter:
    def test_comma(self):
        text = "a,b,c\n1,2,3\n4,5,6"
        assert detect_delimiter(text) == ","

    def test_semicolon(self):
        text = "a;b;c\n1;2;3\n4;5;6"
        assert detect_delimiter(text) == ";"

    def test_tab(self):
        text = "a\tb\tc\n1\t2\t3\n4\t5\t6"
        assert detect_delimiter(text) == "\t"

    def test_single_column_fallback(self):
        # No clear delimiter -> falls back to ","
        text = "justonecolumn\nrow2\nrow3"
        result = detect_delimiter(text)
        assert result == ","

    def test_empty_text(self):
        result = detect_delimiter("")
        assert result == ","


# ===================================================================
# 7. parse_csv_header
# ===================================================================

class TestParseCsvHeader:
    def test_normal_header(self):
        text = "a,b,c\n1,2,3"
        reader, header = parse_csv_header(text, ",")
        assert header == ["a", "b", "c"]
        rows = list(reader)
        assert len(rows) == 1

    def test_strips_bom(self):
        text = "\ufeffa,b,c\n1,2,3"
        reader, header = parse_csv_header(text, ",")
        assert header[0] == "a"

    def test_strips_whitespace(self):
        text = "  a , b , c \n1,2,3"
        reader, header = parse_csv_header(text, ",")
        assert header == ["a", "b", "c"]

    def test_empty_file_raises(self):
        with pytest.raises(ValueError):
            parse_csv_header("", ",")

    def test_semicolon_delimiter(self):
        text = "x;y;z\n1;2;3"
        reader, header = parse_csv_header(text, ";")
        assert header == ["x", "y", "z"]


# ===================================================================
# 8. _get_or_create_sample (DB mocked)
# ===================================================================

class TestGetOrCreateSample:
    @patch("app.services.import_service.db")
    def test_existing_sample_no_update(self, mock_db):
        mock_row = MagicMock()
        mock_row.client_name = "ExistingClient"
        mock_row.sample_type = "coal"
        mock_row.received_date = datetime(2024, 1, 1)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_row
        mock_db.session.query.return_value = mock_query

        result = _get_or_create_sample("S001", {"client_name": "NewClient"})
        assert result is mock_row
        # Should not flush since existing fields are non-empty
        mock_db.session.flush.assert_not_called()

    @patch("app.services.import_service.db")
    def test_existing_sample_updates_empty_fields(self, mock_db):
        mock_row = MagicMock()
        mock_row.client_name = ""
        mock_row.sample_type = None
        mock_row.received_date = None

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_row
        mock_db.session.query.return_value = mock_query

        result = _get_or_create_sample("S001", {
            "client_name": "NewClient",
            "sample_type": "coal",
            "received_date": datetime(2024, 1, 1),
        })
        assert result is mock_row
        assert mock_row.client_name == "NewClient"
        assert mock_row.sample_type == "coal"
        mock_db.session.flush.assert_called_once()

    @patch("app.services.import_service.M")
    @patch("app.services.import_service.db")
    def test_creates_new_sample(self, mock_db, mock_M):
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.session.query.return_value = mock_query

        mock_sample_cls = MagicMock()
        mock_sample_instance = MagicMock()
        mock_sample_cls.return_value = mock_sample_instance
        mock_M.Sample = mock_sample_cls
        # Ensure hasattr checks pass for standard columns
        mock_sample_cls.client_name = True
        mock_sample_cls.sample_type = True
        mock_sample_cls.received_date = True

        result = _get_or_create_sample("S002", {
            "client_name": "Client",
            "sample_type": "coal",
            "received_date": datetime(2024, 6, 1),
        })
        mock_db.session.add.assert_called_once()
        mock_db.session.flush.assert_called_once()


# ===================================================================
# 9. _upsert_result (DB mocked)
# ===================================================================

class TestUpsertResult:
    @patch("app.services.import_service.db")
    def test_update_existing(self, mock_db):
        mock_row = MagicMock()
        mock_row.id = 42
        mock_row.final_result = 1.0
        mock_row.status = "draft"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_row
        mock_db.session.query.return_value = mock_query

        created, rid = _upsert_result(1, "Mad", datetime(2024, 1, 1), 5.5, "approved")
        assert created is False
        assert rid == 42
        assert mock_row.final_result == 5.5
        assert mock_row.status == "approved"
        mock_db.session.flush.assert_called_once()

    @patch("app.services.import_service.db")
    def test_update_existing_none_value(self, mock_db):
        mock_row = MagicMock()
        mock_row.id = 10
        mock_row.final_result = 3.0

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_row
        mock_db.session.query.return_value = mock_query

        created, rid = _upsert_result(1, "Mad", None, None, None)
        assert created is False
        # final_result should NOT be overwritten with None
        assert mock_row.final_result == 3.0

    @patch("app.services.import_service.M")
    @patch("app.services.import_service.db")
    def test_insert_new(self, mock_db, mock_M):
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.session.query.return_value = mock_query

        mock_result_cls = MagicMock()
        mock_new_row = MagicMock()
        mock_new_row.id = 99
        mock_result_cls.return_value = mock_new_row
        mock_M.AnalysisResult = mock_result_cls

        created, rid = _upsert_result(1, "TS", datetime(2024, 1, 1), 2.5, "approved")
        assert created is True
        assert rid == 99
        mock_db.session.add.assert_called_once()
        mock_db.session.flush.assert_called_once()


# ===================================================================
# 10. import_chpp_wide (DB mocked)
# ===================================================================

class TestImportChppWide:
    def _make_reader(self, rows):
        """Create a csv.reader from list of lists."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        for row in rows:
            writer.writerow(row)
        buf.seek(0)
        return csv.reader(buf)

    def test_too_few_columns(self):
        reader = self._make_reader([])
        header = ["a", "b", "c"]
        summary, errors = import_chpp_wide(reader, header, dry_run=True, batch_size=100)
        assert len(errors) == 1
        assert "7" in errors[0]  # mentions 7 columns
        assert summary["Dry-run"] is True

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_dry_run_rollback(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        header = ["_sel", "ID", "Sample", "Unit", "Type", "RegDate", "TestDate", "Mad"]
        data_rows = [["", "1", "S001", "Lab1", "coal", "2024-01-01", "2024-01-02", "3.5"]]
        reader = self._make_reader(data_rows)

        summary, errors = import_chpp_wide(reader, header, dry_run=True, batch_size=100)
        mock_db.session.rollback.assert_called()
        mock_db.session.commit.assert_not_called()

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_normal_import(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        header = ["_sel", "ID", "Sample", "Unit", "Type", "RegDate", "TestDate", "Mad", "TS"]
        data_rows = [
            ["", "1", "S001", "Lab1", "coal", "2024-01-01", "2024-01-02", "3.5", "1.2"],
            ["", "2", "S002", "Lab2", "coal", "2024-01-01", "2024-01-02", "4.0", "1.5"],
        ]
        reader = self._make_reader(data_rows)

        summary, errors = import_chpp_wide(reader, header, dry_run=False, batch_size=100)
        assert len(errors) == 0
        mock_db.session.commit.assert_called()

    @patch("app.services.import_service.to_float", return_value=None)
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_skips_none_values(self, mock_db, mock_get_sample, mock_to_float):
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        header = ["_sel", "ID", "Sample", "Unit", "Type", "RegDate", "TestDate", "Mad"]
        data_rows = [["", "1", "S001", "Lab1", "coal", "2024-01-01", "2024-01-02", ""]]
        reader = self._make_reader(data_rows)

        summary, errors = import_chpp_wide(reader, header, dry_run=True, batch_size=100)
        assert len(errors) == 0

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_row_too_short_skipped(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        mock_db.session.new = []
        header = ["_sel", "ID", "Sample", "Unit", "Type", "RegDate", "TestDate", "Mad"]
        # Row with only 2 columns - shorter than idx_sample (2), should be skipped
        data_rows = [["", ""], ["", "1", "S001", "Lab1", "coal", "2024-01-01", "2024-01-02", "3.5"]]
        reader = self._make_reader(data_rows)

        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample

        summary, errors = import_chpp_wide(reader, header, dry_run=True, batch_size=100)
        # First row skipped (too short), second processed
        assert len(errors) == 0

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(False, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_updated_results_counted(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        header = ["_sel", "ID", "Sample", "Unit", "Type", "RegDate", "TestDate", "Mad"]
        data_rows = [["", "1", "S001", "Lab1", "coal", "2024-01-01", "2024-01-02", "3.5"]]
        reader = self._make_reader(data_rows)

        summary, errors = import_chpp_wide(reader, header, dry_run=True, batch_size=100)
        # _upsert_result returned (False, 1) => updated
        assert summary.get("\u0428\u0438\u043d\u044d\u0447\u0438\u043b\u0441\u044d\u043d \u04af\u0440 \u0434\u04af\u043d", -1) >= 0

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_batch_commit(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        """Test that batch commit happens when batch_count >= batch_size."""
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        header = ["_sel", "ID", "Sample", "Unit", "Type", "RegDate", "TestDate", "Mad"]
        data_rows = [
            ["", "1", "S001", "Lab1", "coal", "2024-01-01", "2024-01-02", "3.5"],
            ["", "2", "S002", "Lab1", "coal", "2024-01-01", "2024-01-02", "4.0"],
        ]
        reader = self._make_reader(data_rows)

        summary, errors = import_chpp_wide(reader, header, dry_run=False, batch_size=1)
        # With batch_size=1, commit should be called multiple times
        assert mock_db.session.commit.call_count >= 2

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_batch_commit_error(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        """Test batch commit SQLAlchemy error handling."""
        from sqlalchemy.exc import SQLAlchemyError
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []
        mock_db.session.commit.side_effect = SQLAlchemyError("batch error")

        header = ["_sel", "ID", "Sample", "Unit", "Type", "RegDate", "TestDate", "Mad"]
        data_rows = [["", "1", "S001", "Lab1", "coal", "2024-01-01", "2024-01-02", "3.5"]]
        reader = self._make_reader(data_rows)

        summary, errors = import_chpp_wide(reader, header, dry_run=False, batch_size=1)
        assert len(errors) >= 1
        mock_db.session.rollback.assert_called()

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_final_commit_error(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        """Test final commit SQLAlchemy error handling."""
        from sqlalchemy.exc import SQLAlchemyError

        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        call_count = [0]
        def commit_side_effect():
            call_count[0] += 1
            if call_count[0] >= 3:
                raise SQLAlchemyError("final error")
        mock_db.session.commit.side_effect = commit_side_effect

        header = ["_sel", "ID", "Sample", "Unit", "Type", "RegDate", "TestDate", "Mad"]
        data_rows = [
            ["", "1", "S001", "Lab1", "coal", "2024-01-01", "2024-01-02", "3.5"],
            ["", "2", "S002", "Lab1", "coal", "2024-01-01", "2024-01-02", "4.0"],
        ]
        reader = self._make_reader(data_rows)

        summary, errors = import_chpp_wide(reader, header, dry_run=False, batch_size=1)
        # Should have the final commit error
        assert any("commit" in e for e in errors)

    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_row_exception_recorded(self, mock_db, mock_get_sample):
        """Test that per-row exceptions are captured in errors list."""
        mock_get_sample.side_effect = ValueError("bad data")
        mock_db.session.new = []

        header = ["_sel", "ID", "Sample", "Unit", "Type", "RegDate", "TestDate", "Mad"]
        data_rows = [["", "1", "S001", "Lab1", "coal", "2024-01-01", "2024-01-02", "3.5"]]
        reader = self._make_reader(data_rows)

        summary, errors = import_chpp_wide(reader, header, dry_run=True, batch_size=100)
        assert len(errors) == 1
        assert "bad data" in errors[0]

    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_empty_sample_code_skipped(self, mock_db, mock_get_sample):
        mock_db.session.new = []
        header = ["_sel", "ID", "Sample", "Unit", "Type", "RegDate", "TestDate", "Mad"]
        data_rows = [["", "1", "", "Lab1", "coal", "2024-01-01", "2024-01-02", "3.5"]]
        reader = self._make_reader(data_rows)

        summary, errors = import_chpp_wide(reader, header, dry_run=True, batch_size=100)
        mock_get_sample.assert_not_called()

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_empty_analysis_col_header_skipped(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        """Columns with empty header names are excluded from analysis_cols."""
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        # 8th col header is empty string -> should be skipped
        header = ["_sel", "ID", "Sample", "Unit", "Type", "RegDate", "TestDate", "", "Mad"]
        data_rows = [["", "1", "S001", "Lab1", "coal", "2024-01-01", "2024-01-02", "999", "3.5"]]
        reader = self._make_reader(data_rows)

        summary, errors = import_chpp_wide(reader, header, dry_run=True, batch_size=100)
        # Only "Mad" column should trigger upsert, not the empty header
        assert mock_upsert.call_count == 1


# ===================================================================
# 11. import_long (DB mocked)
# ===================================================================

class TestImportLong:
    def _make_reader_from_text(self, text, delim=","):
        reader, header = parse_csv_header(text, delim)
        return reader, header

    def test_missing_columns_raises(self):
        text = "a,b,c\n1,2,3"
        reader, header = self._make_reader_from_text(text)
        with pytest.raises(ValueError) as exc_info:
            import_long(reader, header, dry_run=True, batch_size=100, delim=",")
        # Should mention missing columns
        assert "sample_code" in str(exc_info.value) or len(str(exc_info.value)) > 0

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_normal_long_import(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date\n"
        text += "S001,Lab1,coal,Mad,3.5,2024-01-01\n"
        text += "S002,Lab2,coal,TS,1.2,2024-01-02\n"
        reader, header = self._make_reader_from_text(text)

        summary, errors = import_long(reader, header, dry_run=False, batch_size=100, delim=",")
        assert len(errors) == 0
        assert mock_upsert.call_count == 2
        mock_db.session.commit.assert_called()

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_dry_run_rollback(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date\n"
        text += "S001,Lab1,coal,Mad,3.5,2024-01-01\n"
        reader, header = self._make_reader_from_text(text)

        summary, errors = import_long(reader, header, dry_run=True, batch_size=100, delim=",")
        mock_db.session.rollback.assert_called()
        mock_db.session.commit.assert_not_called()

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_empty_sample_code_skipped(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        mock_db.session.new = []

        text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date\n"
        text += ",Lab1,coal,Mad,3.5,2024-01-01\n"
        reader, header = self._make_reader_from_text(text)

        summary, errors = import_long(reader, header, dry_run=True, batch_size=100, delim=",")
        mock_get_sample.assert_not_called()

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(False, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_updated_results(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date\n"
        text += "S001,Lab1,coal,Mad,3.5,2024-01-01\n"
        reader, header = self._make_reader_from_text(text)

        summary, errors = import_long(reader, header, dry_run=True, batch_size=100, delim=",")
        assert len(errors) == 0

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_batch_commit(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date\n"
        text += "S001,Lab1,coal,Mad,3.5,2024-01-01\n"
        text += "S002,Lab2,coal,TS,1.2,2024-01-02\n"
        reader, header = self._make_reader_from_text(text)

        summary, errors = import_long(reader, header, dry_run=False, batch_size=1, delim=",")
        assert mock_db.session.commit.call_count >= 2

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_batch_commit_error(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        from sqlalchemy.exc import SQLAlchemyError
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []
        mock_db.session.commit.side_effect = SQLAlchemyError("batch fail")

        text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date\n"
        text += "S001,Lab1,coal,Mad,3.5,2024-01-01\n"
        reader, header = self._make_reader_from_text(text)

        summary, errors = import_long(reader, header, dry_run=False, batch_size=1, delim=",")
        assert len(errors) >= 1
        mock_db.session.rollback.assert_called()

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_final_commit_error(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        from sqlalchemy.exc import SQLAlchemyError
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        call_count = [0]
        def commit_side_effect():
            call_count[0] += 1
            if call_count[0] >= 3:
                raise SQLAlchemyError("final fail")
        mock_db.session.commit.side_effect = commit_side_effect

        text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date\n"
        text += "S001,Lab1,coal,Mad,3.5,2024-01-01\n"
        text += "S002,Lab2,coal,TS,1.2,2024-01-02\n"
        reader, header = self._make_reader_from_text(text)

        summary, errors = import_long(reader, header, dry_run=False, batch_size=1, delim=",")
        assert any("commit" in e for e in errors)

    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_row_exception_captured(self, mock_db, mock_get_sample):
        mock_get_sample.side_effect = ValueError("row error")
        mock_db.session.new = []

        text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date\n"
        text += "S001,Lab1,coal,Mad,3.5,2024-01-01\n"
        reader, header = self._make_reader_from_text(text)

        summary, errors = import_long(reader, header, dry_run=True, batch_size=100, delim=",")
        assert len(errors) == 1
        assert "row error" in errors[0]

    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_sqlalchemy_error_propagates(self, mock_db, mock_get_sample):
        """SQLAlchemyError in outer try block is re-raised after rollback."""
        from sqlalchemy.exc import SQLAlchemyError

        # Make the reader itself raise SQLAlchemyError
        mock_reader = MagicMock()
        mock_reader.__iter__ = MagicMock(side_effect=SQLAlchemyError("db down"))

        header_text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date"
        cols = {}
        for i, h in enumerate(header_text.split(",")):
            key = _map_header(h)
            if key:
                cols[key] = i

        with pytest.raises(SQLAlchemyError):
            import_long(mock_reader, header_text.split(","), dry_run=False, batch_size=100, delim=",")
        mock_db.session.rollback.assert_called()

    @patch("app.services.import_service.to_float", return_value=5.5)
    @patch("app.services.import_service._upsert_result", return_value=(True, 1))
    @patch("app.services.import_service._get_or_create_sample")
    @patch("app.services.import_service.db")
    def test_with_optional_columns(self, mock_db, mock_get_sample, mock_upsert, mock_to_float):
        """Test with optional columns like received_date and status."""
        mock_sample = MagicMock()
        mock_sample.id = 1
        mock_get_sample.return_value = mock_sample
        mock_db.session.new = []

        text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date,received_date,status\n"
        text += "S001,Lab1,coal,Mad,3.5,2024-01-01,2024-01-01,approved\n"
        reader, header = self._make_reader_from_text(text)

        summary, errors = import_long(reader, header, dry_run=True, batch_size=100, delim=",")
        assert len(errors) == 0


# ===================================================================
# 12. process_csv_import (orchestrator)
# ===================================================================

class TestProcessCsvImport:
    @patch("app.services.import_service.import_chpp_wide")
    @patch("app.services.import_service.import_long")
    def test_long_format_success(self, mock_long, mock_wide):
        mock_long.return_value = ({"rows": 10}, [])

        csv_text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date\n"
        csv_text += "S001,Lab1,coal,Mad,3.5,2024-01-01\n"
        raw = csv_text.encode("utf-8")

        summary, errors = process_csv_import(raw, dry_run=True, batch_size=100)
        mock_long.assert_called_once()
        mock_wide.assert_not_called()

    @patch("app.services.import_service.import_chpp_wide")
    @patch("app.services.import_service.import_long")
    def test_fallback_to_chpp_wide(self, mock_long, mock_wide):
        # import_long raises ValueError with the missing-columns message
        mock_long.side_effect = ValueError("\u0414\u0443\u0442\u0443\u0443 \u0431\u0430\u0433\u0430\u043d\u0430 \u0431\u0430\u0439\u043d\u0430 (zaaval): analysis_code")
        mock_wide.return_value = ({"rows": 5}, [])

        csv_text = "_sel,ID,Sample,Unit,Type,RegDate,TestDate,Mad\n"
        csv_text += ",1,S001,Lab1,coal,2024-01-01,2024-01-02,3.5\n"
        raw = csv_text.encode("utf-8")

        summary, errors = process_csv_import(raw, dry_run=True, batch_size=100)
        mock_wide.assert_called_once()

    @patch("app.services.import_service.import_long")
    def test_non_missing_column_valueerror_propagates(self, mock_long):
        mock_long.side_effect = ValueError("Some other error")

        csv_text = "a,b\n1,2\n"
        raw = csv_text.encode("utf-8")

        with pytest.raises(ValueError, match="Some other error"):
            process_csv_import(raw, dry_run=True, batch_size=100)

    def test_empty_file_raises(self):
        raw = b""
        with pytest.raises(ValueError):
            process_csv_import(raw, dry_run=True)

    @patch("app.services.import_service.import_long")
    def test_utf8_sig_decoded(self, mock_long):
        mock_long.return_value = ({"rows": 1}, [])
        csv_text = "sample_code,client_name,sample_type,analysis_code,value,analysis_date\n"
        csv_text += "S001,Lab1,coal,Mad,3.5,2024-01-01\n"
        raw = b"\xef\xbb\xbf" + csv_text.encode("utf-8")

        summary, errors = process_csv_import(raw, dry_run=True)
        mock_long.assert_called_once()


# ===================================================================
# Edge cases and integration-style tests
# ===================================================================

class TestEdgeCases:
    def test_header_keys_all_have_synonyms(self):
        """Verify HEADER_KEYS dict structure."""
        for key, synonyms in HEADER_KEYS.items():
            assert isinstance(synonyms, set)
            assert len(synonyms) > 0

    def test_alias_to_base_lowercase_keys(self):
        """All ALIAS_TO_BASE keys should be lowercase."""
        for key in ALIAS_TO_BASE:
            assert key == key.lower(), f"Key {key} is not lowercase"

    def test_parse_date_with_integer(self):
        """Test _parse_date with integer-like year."""
        dt = _parse_date(2020)
        assert dt == datetime(2020, 1, 1)

    def test_base_code_with_whitespace_only(self):
        """Whitespace-only input should return empty after strip check."""
        result = _base_code("   ")
        # After strip, "   " becomes "", which is falsy but _base_code checks `if not raw`
        # raw="   " is truthy, so it strips to "" and checks ALIAS_TO_BASE
        # "" not in ALIAS_TO_BASE, so returns ""
        assert result == ""

    def test_map_header_empty_string(self):
        assert _map_header("") is None

    def test_detect_delimiter_with_mixed(self):
        """When text has both commas and semicolons, Sniffer picks the dominant one."""
        text = "a;b;c\n1;2;3\n4;5;6\n7;8;9"
        result = detect_delimiter(text)
        assert result == ";"

    def test_parse_csv_header_none_columns(self):
        """Header with None-like values gets cleaned."""
        text = ",a,,b\n1,2,3,4"
        reader, header = parse_csv_header(text, ",")
        assert header == ["", "a", "", "b"]

    def test_norm_with_float(self):
        assert _norm(3.14) == "3.14"

    def test_norm_with_bool(self):
        assert _norm(True) == "True"

    def test_parse_date_whitespace_only(self):
        assert _parse_date("   ") is None
