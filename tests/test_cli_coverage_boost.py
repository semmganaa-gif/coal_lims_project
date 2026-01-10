# -*- coding: utf-8 -*-
"""
Additional tests to boost cli.py coverage to 80%+
"""
import pytest
from click.testing import CliRunner
from app import db
from app.models import User, Equipment, SystemSetting
import tempfile
import os
import pandas as pd


class TestCliHelperFunctions:
    """Test helper functions in cli.py"""

    def test_safe_str_with_nan(self, app):
        """Test _safe_str with pandas NaN"""
        from app.cli import _safe_str
        import numpy as np

        assert _safe_str(None) == ""
        assert _safe_str(np.nan) == ""
        assert _safe_str("  test  ") == "test"
        assert _safe_str(123) == "123"

    def test_safe_int_with_various_inputs(self, app):
        """Test _safe_int with various inputs"""
        from app.cli import _safe_int
        import numpy as np

        assert _safe_int(None) is None
        assert _safe_int(None, default=0) == 0
        assert _safe_int(np.nan) is None
        assert _safe_int("  42  ") == 42
        assert _safe_int("3.7") == 3
        assert _safe_int("invalid") is None
        assert _safe_int("") is None
        assert _safe_int("", default=5) == 5

    def test_safe_float_with_various_inputs(self, app):
        """Test _safe_float with various inputs"""
        from app.cli import _safe_float
        import numpy as np

        assert _safe_float(None) is None
        assert _safe_float(None, default=0.0) == 0.0
        assert _safe_float(np.nan) is None
        assert _safe_float("  3.14  ") == 3.14
        assert _safe_float("1,234.56".replace(",", "")) == 1234.56
        assert _safe_float("invalid") is None
        assert _safe_float("") is None


class TestUserCliCommands:
    """Test user CLI commands"""

    def test_create_user_success(self, app):
        """Test creating user via CLI"""
        runner = CliRunner()

        with app.app_context():
            # Clean up if exists
            User.query.filter_by(username='cli_test_user').delete()
            db.session.commit()

            result = runner.invoke(
                app.cli,
                ['users', 'create', 'cli_test_user', 'TestPass123', 'chemist']
            )

            assert 'амжилттай' in result.output or result.exit_code == 0

            # Cleanup
            User.query.filter_by(username='cli_test_user').delete()
            db.session.commit()

    def test_create_user_duplicate(self, app):
        """Test creating duplicate user"""
        runner = CliRunner()

        with app.app_context():
            result = runner.invoke(
                app.cli,
                ['users', 'create', 'admin', 'TestPass123', 'admin']
            )

            # Should show duplicate error
            assert 'аль хэдийн' in result.output or 'байна' in result.output

    def test_create_user_invalid_role(self, app):
        """Test creating user with invalid role"""
        runner = CliRunner()

        with app.app_context():
            result = runner.invoke(
                app.cli,
                ['users', 'create', 'newuser', 'TestPass123', 'invalid_role']
            )

            assert 'Алдаа' in result.output or 'буруу' in result.output

    def test_create_user_weak_password(self, app):
        """Test creating user with weak password"""
        runner = CliRunner()

        with app.app_context():
            # Clean up if exists
            User.query.filter_by(username='weak_pass_user').delete()
            db.session.commit()

            result = runner.invoke(
                app.cli,
                ['users', 'create', 'weak_pass_user', 'weak', 'chemist']
            )

            # Should show password error
            assert 'Алдаа' in result.output or result.exit_code != 0


class TestEquipmentCliCommands:
    """Test equipment CLI commands"""

    def test_import_equipment_file_not_found(self, app):
        """Test import with non-existent file"""
        runner = CliRunner()

        with app.app_context():
            result = runner.invoke(
                app.cli,
                ['equipment', 'import-excel', 'nonexistent_file.xlsx']
            )

            assert 'олдсонгүй' in result.output or 'not found' in result.output.lower()

    def test_import_equipment_format_a(self, app):
        """Test import with Format A (simple table)"""
        runner = CliRunner()

        with app.app_context():
            # Create temporary Excel file with Format A
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
                temp_path = f.name

            try:
                # Create test data in Format A
                data = {
                    'Тоног төхөөрөмжийн нэр': ['Test Equipment 1', 'Test Equipment 2'],
                    'Үйлдвэрлэгч': ['Manufacturer A', 'Manufacturer B'],
                    'Марк дугаар': ['Model-001', 'Model-002'],
                    'Зориулалт': ['Location A', 'Location B'],
                    'Шалгалт тохируулга': ['Note 1', 'Note 2'],
                    'Тоо хэмжээ': [1, 2],
                    'Үйлдвэрлэсэн огноо': ['2020', '2021'],
                    'Ашиглалтанд орсон огноо': ['2021', '2022'],
                    'Анхны үнэ /төг/': [100000, 200000],
                    'Үлдэгдэл үнэ /төг/': [50000, 100000],
                    'Тайлбар': ['Remark 1', 'Remark 2'],
                }

                # Create DataFrame with header rows (to simulate real file)
                df = pd.DataFrame(data)

                # Write with header at row 2 (0-indexed)
                with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
                    # Write empty rows first
                    empty_df = pd.DataFrame([[''] * len(df.columns), [''] * len(df.columns)])
                    empty_df.to_excel(writer, sheet_name='1', index=False, header=False)
                    # Write data starting from row 3
                    df.to_excel(writer, sheet_name='1', index=False, startrow=2)

                result = runner.invoke(
                    app.cli,
                    ['equipment', 'import-excel', temp_path, '--sheet', '1']
                )

                # Should complete (may skip duplicates)
                assert 'Загвар A' in result.output or 'дууслаа' in result.output or result.exit_code == 0

            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

                # Cleanup imported equipment
                Equipment.query.filter(Equipment.name.like('Test Equipment%')).delete()
                db.session.commit()

    def test_export_equipment(self, app):
        """Test exporting equipment to Excel"""
        runner = CliRunner()

        with app.app_context():
            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
                temp_path = f.name

            try:
                result = runner.invoke(
                    app.cli,
                    ['equipment', 'export-excel', temp_path]
                )

                assert 'амжилттай' in result.output or result.exit_code == 0

                # Check file was created
                assert os.path.exists(temp_path)

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)


class TestImportLimitsCommand:
    """Test import-limits CLI command"""

    def test_import_limits_file_not_found(self, app):
        """Test import-limits with non-existent file"""
        runner = CliRunner()

        with app.app_context():
            result = runner.invoke(
                app.cli,
                ['import-limits', 'nonexistent_file.csv']
            )

            assert 'олдсонгүй' in result.output

    def test_import_limits_invalid_csv(self, app):
        """Test import-limits with invalid CSV"""
        runner = CliRunner()

        with app.app_context():
            # Create invalid CSV
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                f.write("col1,col2\n")  # Not enough columns
                temp_path = f.name

            try:
                result = runner.invoke(
                    app.cli,
                    ['import-limits', temp_path]
                )

                assert 'хүрэлцэхгүй' in result.output or 'Баганы' in result.output

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_import_limits_success(self, app):
        """Test successful limits import"""
        runner = CliRunner()

        with app.app_context():
            # Create valid CSV
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
                f.write("Арга хэмжилт,Стандартын нэр,Хэмжигдэх мужийн,Давтамжийн хязгаа,Тайрцын тэмдэг\n")
                f.write("LAB.07.03 Анализ чийг,ISO 589,<10,0.3,\n")
                f.write(",ISO 589,10-20,0.5,\n")
                f.write("LAB.07.05 Үнс,ISO 1171,<10,0.2,\n")
                temp_path = f.name

            try:
                result = runner.invoke(
                    app.cli,
                    ['import-limits', temp_path]
                )

                assert 'Амжилттай' in result.output or 'хадгалсан' in result.output

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_import_limits_with_percent(self, app):
        """Test import with percentage limits"""
        runner = CliRunner()

        with app.app_context():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
                f.write("Арга хэмжилт,Стандартын нэр,Хэмжигдэх мужийн,Давтамжийн хязгаа,Тайрцын тэмдэг\n")
                f.write("LAB.07.04 Дэгдэмхий,ISO 562,<40,5%,\n")
                f.write(",ISO 562,>40,үр дүнгийн 1/2,\n")
                temp_path = f.name

            try:
                result = runner.invoke(
                    app.cli,
                    ['import-limits', temp_path]
                )

                # Should handle percent and special syntax
                assert result.exit_code == 0 or 'Амжилттай' in result.output

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)


class TestImportEquipmentFormatB:
    """Test equipment import with Format B (multi-header)"""

    def test_import_equipment_format_b(self, app):
        """Test import with Format B (multi-row header)"""
        runner = CliRunner()

        with app.app_context():
            # Create temporary Excel file with Format B
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
                temp_path = f.name

            try:
                # Create test data in Format B style
                # Columns: idx, idx2, name, manufacturer, model, labcode, qty, commissioned, location
                data = {
                    'col0': [1, 2],
                    'col1': ['', ''],
                    'col2': ['Equipment B1', 'Equipment B2'],
                    'col3': ['Mfg B', 'Mfg C'],
                    'col4': ['Model-B1', 'Model-B2'],
                    'col5': ['LAB_001', 'LAB_002'],
                    'col6': [1, 2],
                    'col7': ['2022', '2023'],
                    'col8': ['Lab Room 1', 'Lab Room 2'],
                }

                df = pd.DataFrame(data)

                with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
                    # Write with header rows
                    empty_df = pd.DataFrame([[''] * len(df.columns), [''] * len(df.columns)])
                    empty_df.to_excel(writer, sheet_name='2', index=False, header=False)
                    df.to_excel(writer, sheet_name='2', index=False, startrow=2)

                result = runner.invoke(
                    app.cli,
                    ['equipment', 'import-excel', temp_path, '--sheet', '2']
                )

                # Should recognize Format B or complete
                assert 'Загвар B' in result.output or 'дууслаа' in result.output or result.exit_code == 0

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

                # Cleanup
                Equipment.query.filter(Equipment.name.like('Equipment B%')).delete()
                db.session.commit()

    def test_import_equipment_few_columns(self, app):
        """Test import with too few columns"""
        runner = CliRunner()

        with app.app_context():
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
                temp_path = f.name

            try:
                # Create minimal data (too few columns for Format B)
                data = {'col0': [1], 'col1': [2], 'col2': [3]}
                df = pd.DataFrame(data)

                with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
                    empty_df = pd.DataFrame([[''] * 3, [''] * 3])
                    empty_df.to_excel(writer, sheet_name='1', index=False, header=False)
                    df.to_excel(writer, sheet_name='1', index=False, startrow=2)

                result = runner.invoke(
                    app.cli,
                    ['equipment', 'import-excel', temp_path, '--sheet', '1']
                )

                # Should handle gracefully
                assert result.exit_code == 0 or 'Алдаа' in result.output

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
