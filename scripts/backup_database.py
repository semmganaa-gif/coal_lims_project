# scripts/backup_database.py
# -*- coding: utf-8 -*-
"""
Database backup script

SQLite болон PostgreSQL database backup хийх.
Windows Task Scheduler эсвэл cron-оор автоматжуулж болно.

Жишээ:
    # PostgreSQL backup (default)
    python scripts/backup_database.py

    # SQLite backup
    python scripts/backup_database.py --sqlite --db-path instance/coal_lims.db

    # Custom backup directory
    python scripts/backup_database.py --backup-dir D:/backups

    # Keep more backups
    python scripts/backup_database.py --keep 30
"""

import os
import shutil
import subprocess
from datetime import datetime
import argparse


def backup_postgresql(backup_dir='backups', db_name='coal_lims',
                      db_user='postgres', db_host='localhost', db_port='5432'):
    """
    PostgreSQL database backup хийх (pg_dump ашиглан)

    Args:
        backup_dir: Backup хадгалах хавтас
        db_name: Database нэр
        db_user: Database хэрэглэгч
        db_host: Database host
        db_port: Database port

    Returns:
        str: Backup файлын нэр
    """
    # Backup хавтас үүсгэх
    os.makedirs(backup_dir, exist_ok=True)

    # Timestamp үүсгэх
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'coal_lims_{timestamp}.sql')

    # pg_dump команд
    # Windows-д pg_dump.exe замыг олох
    pg_dump_paths = [
        'pg_dump',  # PATH-д байвал
        r'C:\Program Files\PostgreSQL\18\bin\pg_dump.exe',
        r'C:\Program Files\PostgreSQL\17\bin\pg_dump.exe',
        r'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe',
        r'C:\Program Files\PostgreSQL\15\bin\pg_dump.exe',
    ]

    pg_dump_cmd = None
    for path in pg_dump_paths:
        if os.path.exists(path) or path == 'pg_dump':
            pg_dump_cmd = path
            break

    if not pg_dump_cmd:
        raise FileNotFoundError("pg_dump олдсонгүй. PostgreSQL суулгасан эсэхийг шалгана уу.")

    # pg_dump ажиллуулах
    cmd = [
        pg_dump_cmd,
        '-h', db_host,
        '-p', db_port,
        '-U', db_user,
        '-d', db_name,
        '-f', backup_file,
        '--no-password',  # .pgpass файл ашиглах
        '--verbose'
    ]

    print(f"🔄 PostgreSQL backup эхэллээ...")
    print(f"   Database: {db_name}@{db_host}:{db_port}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 минут timeout
        )

        if result.returncode != 0:
            raise Exception(f"pg_dump алдаа: {result.stderr}")

    except subprocess.TimeoutExpired:
        raise Exception("pg_dump timeout (5 минут)")

    # Backup файлын хэмжээ авах
    file_size = os.path.getsize(backup_file)
    file_size_mb = file_size / (1024 * 1024)

    print(f"✅ PostgreSQL backup амжилттай:")
    print(f"   Файл: {backup_file}")
    print(f"   Хэмжээ: {file_size_mb:.2f} MB")

    return backup_file


def backup_sqlite(db_path='instance/coal_lims.db', backup_dir='backups'):
    """
    SQLite database backup хийх

    Args:
        db_path: Database файлын зам
        backup_dir: Backup хадгалах хавтас

    Returns:
        str: Backup файлын нэр
    """
    # Backup хавтас үүсгэх
    os.makedirs(backup_dir, exist_ok=True)

    # Timestamp үүсгэх
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'coal_lims_{timestamp}.db')

    # Database файл байгаа эсэхийг шалгах
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database файл олдсонгүй: {db_path}")

    # Backup хийх (SQLite - simple copy)
    shutil.copy2(db_path, backup_file)

    # Backup файлын хэмжээ авах
    file_size = os.path.getsize(backup_file)
    file_size_mb = file_size / (1024 * 1024)

    print(f"✅ SQLite backup амжилттай:")
    print(f"   Файл: {backup_file}")
    print(f"   Хэмжээ: {file_size_mb:.2f} MB")

    return backup_file


def cleanup_old_backups(backup_dir='backups', keep_count=10):
    """
    Хуучин backup файлуудыг устгах

    Args:
        backup_dir: Backup хавтас
        keep_count: Хадгалах backup-ын тоо (сүүлийн N-г хадгална)
    """
    if not os.path.exists(backup_dir):
        return

    # Бүх backup файлуудыг авах (.db, .sql)
    backup_files = [
        os.path.join(backup_dir, f)
        for f in os.listdir(backup_dir)
        if f.endswith(('.db', '.sql'))
    ]

    # Огноогоор эрэмбэлэх (хамгийн шинийг эхэнд)
    backup_files.sort(key=os.path.getmtime, reverse=True)

    # Хуучин файлуудыг устгах
    files_to_delete = backup_files[keep_count:]

    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"🗑️  Устгасан: {os.path.basename(file_path)}")
        except OSError as e:
            print(f"⚠️  Устгаж чадсангүй: {file_path} - {e}")

    if files_to_delete:
        print(f"✅ {len(files_to_delete)} хуучин backup устгагдлаа")
    else:
        print(f"ℹ️  Устгах backup байхгүй ({keep_count}-с цөөн)")


def main():
    """Main функц - command line аргументуудыг боловсруулах"""
    parser = argparse.ArgumentParser(
        description='Coal LIMS Database Backup',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Жишээнүүд:
  python scripts/backup_database.py                    # PostgreSQL backup
  python scripts/backup_database.py --sqlite           # SQLite backup
  python scripts/backup_database.py --keep 30          # 30 backup хадгалах
  python scripts/backup_database.py --backup-dir D:/bak  # Custom хавтас
        """
    )

    # Database type
    parser.add_argument(
        '--sqlite',
        action='store_true',
        help='SQLite backup хийх (default: PostgreSQL)'
    )

    # PostgreSQL options
    parser.add_argument(
        '--db-name',
        default='coal_lims',
        help='PostgreSQL database нэр (default: coal_lims)'
    )
    parser.add_argument(
        '--db-user',
        default='postgres',
        help='PostgreSQL хэрэглэгч (default: postgres)'
    )
    parser.add_argument(
        '--db-host',
        default='localhost',
        help='PostgreSQL host (default: localhost)'
    )
    parser.add_argument(
        '--db-port',
        default='5432',
        help='PostgreSQL port (default: 5432)'
    )

    # SQLite options
    parser.add_argument(
        '--db-path',
        default='instance/coal_lims.db',
        help='SQLite файлын зам (default: instance/coal_lims.db)'
    )

    # Common options
    parser.add_argument(
        '--backup-dir',
        default='backups',
        help='Backup хавтас (default: backups)'
    )
    parser.add_argument(
        '--keep',
        type=int,
        default=10,
        help='Хадгалах backup-ын тоо (default: 10)'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Хуучин backup устгахгүй байх'
    )

    args = parser.parse_args()

    try:
        print("=" * 50)
        print("Coal LIMS Database Backup")
        print("=" * 50)
        print(f"Огноо: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Backup хийх
        if args.sqlite:
            backup_file = backup_sqlite(args.db_path, args.backup_dir)
        else:
            backup_file = backup_postgresql(
                backup_dir=args.backup_dir,
                db_name=args.db_name,
                db_user=args.db_user,
                db_host=args.db_host,
                db_port=args.db_port
            )

        print()

        # Хуучин backup-уудыг устгах
        if not args.no_cleanup:
            cleanup_old_backups(args.backup_dir, args.keep)

        print()
        print("=" * 50)
        print("✅ Backup бүрэн амжилттай боллоо!")
        print("=" * 50)

    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ Backup хийхэд алдаа гарлаа: {e}")
        print("=" * 50)
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
