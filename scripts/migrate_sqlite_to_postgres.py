"""
SQLite-аас PostgreSQL руу өгөгдөл шилжүүлэх script

Ашиглах: python scripts/migrate_sqlite_to_postgres.py
"""
import sqlite3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    User, Sample, AnalysisResult, AnalysisType, AnalysisProfile,
    Equipment, MaintenanceLog, Bottle, BottleConstant, UsageLog,
    AnalysisResultLog, SystemSetting, AuditLog, ControlStandard,
    GbwStandard, CorrectiveAction, CustomerComplaint, EnvironmentalLog,
    ProficiencyTest, QCControlChart, MonthlyPlan, StaffSettings
)
from werkzeug.security import generate_password_hash

SQLITE_PATH = 'instance/lims.db'

def get_sqlite_tables(conn):
    """SQLite дахь table-үүдийн жагсаалт авах"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]

def get_table_data(conn, table_name):
    """Table-ийн бүх өгөгдөл авах"""
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM "{table_name}"')
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    return columns, rows

def migrate_users(conn, app):
    """User хүснэгт шилжүүлэх"""
    print("\n=== User хүснэгт шилжүүлж байна... ===")
    columns, rows = get_table_data(conn, 'user')

    with app.app_context():
        for row in rows:
            data = dict(zip(columns, row))
            # Existing user байгаа эсэх шалгах
            existing = User.query.filter_by(username=data.get('username')).first()
            if existing:
                print(f"  Skip: {data.get('username')} (already exists)")
                continue

            user = User(
                id=data.get('id'),
                username=data.get('username'),
                password_hash=data.get('password_hash'),
                role=data.get('role')
            )
            db.session.add(user)
            print(f"  Added: {data.get('username')}")

        db.session.commit()
        print(f"  Total: {len(rows)} users processed")

def migrate_samples(conn, app):
    """Sample хүснэгт шилжүүлэх"""
    print("\n=== Sample хүснэгт шилжүүлж байна... ===")
    columns, rows = get_table_data(conn, 'sample')

    with app.app_context():
        count = 0
        for row in rows:
            data = dict(zip(columns, row))
            existing = Sample.query.get(data.get('id'))
            if existing:
                continue

            sample = Sample()
            for col in columns:
                if hasattr(sample, col) and col != 'id':
                    setattr(sample, col, data.get(col))
            sample.id = data.get('id')
            db.session.add(sample)
            count += 1

        db.session.commit()
        print(f"  Added: {count} samples")

def migrate_analysis_results(conn, app):
    """AnalysisResult хүснэгт шилжүүлэх"""
    print("\n=== AnalysisResult хүснэгт шилжүүлж байна... ===")
    columns, rows = get_table_data(conn, 'analysis_result')

    with app.app_context():
        count = 0
        for row in rows:
            data = dict(zip(columns, row))
            existing = AnalysisResult.query.get(data.get('id'))
            if existing:
                continue

            ar = AnalysisResult()
            for col in columns:
                if hasattr(ar, col) and col != 'id':
                    setattr(ar, col, data.get(col))
            ar.id = data.get('id')
            db.session.add(ar)
            count += 1

        db.session.commit()
        print(f"  Added: {count} analysis results")

def migrate_generic_table(conn, app, table_name, model_class):
    """Generic table шилжүүлэх"""
    print(f"\n=== {table_name} хүснэгт шилжүүлж байна... ===")

    try:
        columns, rows = get_table_data(conn, table_name)
    except Exception as e:
        print(f"  Skip: Table not found in SQLite ({e})")
        return

    with app.app_context():
        count = 0
        for row in rows:
            data = dict(zip(columns, row))

            # Check if exists
            existing = model_class.query.get(data.get('id'))
            if existing:
                continue

            obj = model_class()
            for col in columns:
                if hasattr(obj, col):
                    setattr(obj, col, data.get(col))

            db.session.add(obj)
            count += 1

        try:
            db.session.commit()
            print(f"  Added: {count} rows")
        except Exception as e:
            db.session.rollback()
            print(f"  Error: {e}")

def main():
    print("=" * 60)
    print("SQLite -> PostgreSQL Migration")
    print("=" * 60)

    # SQLite холболт
    if not os.path.exists(SQLITE_PATH):
        print(f"Error: SQLite database not found: {SQLITE_PATH}")
        return

    conn = sqlite3.connect(SQLITE_PATH)

    # SQLite tables шалгах
    tables = get_sqlite_tables(conn)
    print(f"\nSQLite tables found: {len(tables)}")
    for t in tables:
        cursor = conn.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
        count = cursor.fetchone()[0]
        print(f"  {t}: {count} rows")

    # Flask app
    app = create_app()

    # Хүснэгтүүд шилжүүлэх (дараалал чухал - FK constraints!)

    # 1. Users (no dependencies)
    migrate_users(conn, app)

    # 2. Equipment, AnalysisType, AnalysisProfile (no dependencies)
    migrate_generic_table(conn, app, 'equipment', Equipment)
    migrate_generic_table(conn, app, 'analysis_type', AnalysisType)
    migrate_generic_table(conn, app, 'analysis_profiles', AnalysisProfile)

    # 3. Samples (depends on user)
    migrate_samples(conn, app)

    # 4. AnalysisResults (depends on sample, user, equipment)
    migrate_analysis_results(conn, app)

    # 5. Other tables
    migrate_generic_table(conn, app, 'bottle', Bottle)
    migrate_generic_table(conn, app, 'bottle_constant', BottleConstant)
    migrate_generic_table(conn, app, 'usage_logs', UsageLog)
    migrate_generic_table(conn, app, 'analysis_result_log', AnalysisResultLog)
    migrate_generic_table(conn, app, 'system_setting', SystemSetting)
    migrate_generic_table(conn, app, 'audit_log', AuditLog)
    migrate_generic_table(conn, app, 'maintenance_logs', MaintenanceLog)
    migrate_generic_table(conn, app, 'control_standards', ControlStandard)
    migrate_generic_table(conn, app, 'gbw_standards', GbwStandard)
    migrate_generic_table(conn, app, 'corrective_action', CorrectiveAction)
    migrate_generic_table(conn, app, 'customer_complaint', CustomerComplaint)
    migrate_generic_table(conn, app, 'environmental_log', EnvironmentalLog)
    migrate_generic_table(conn, app, 'proficiency_test', ProficiencyTest)
    migrate_generic_table(conn, app, 'qc_control_chart', QCControlChart)
    migrate_generic_table(conn, app, 'monthly_plan', MonthlyPlan)
    migrate_generic_table(conn, app, 'staff_settings', StaffSettings)

    conn.close()

    print("\n" + "=" * 60)
    print("Migration completed!")
    print("=" * 60)

if __name__ == '__main__':
    main()
