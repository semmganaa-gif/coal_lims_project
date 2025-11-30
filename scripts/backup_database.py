# scripts/backup_database.py
# -*- coding: utf-8 -*-
"""
Database backup script

Автомат эсвэл гараар database backup хийх
"""

import os
import shutil
from datetime import datetime
import argparse


def backup_database(db_path='instance/coal_lims.db', backup_dir='backups'):
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
    backup_file = f'{backup_dir}/coal_lims_{timestamp}.db'

    # Database файл байгаа эсэхийг шалгах
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database файл олдсонгүй: {db_path}")

    # Backup хийх (SQLite - simple copy)
    shutil.copy2(db_path, backup_file)

    # Backup файлын хэмжээ авах
    file_size = os.path.getsize(backup_file)
    file_size_mb = file_size / (1024 * 1024)

    print(f"✅ Backup амжилттай үүслээ:")
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

    # Бүх .db файлуудыг авах
    backup_files = [
        os.path.join(backup_dir, f)
        for f in os.listdir(backup_dir)
        if f.endswith('.db')
    ]

    # Огноогоор эрэмбэлэх (хамгийн шинийг эхэнд)
    backup_files.sort(key=os.path.getmtime, reverse=True)

    # Хуучин файлуудыг устгах
    files_to_delete = backup_files[keep_count:]

    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"🗑️  Устгасан: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"⚠️  Устгаж чадсангүй: {file_path} - {e}")

    if files_to_delete:
        print(f"✅ {len(files_to_delete)} хуучин backup устгагдлаа")
    else:
        print(f"ℹ️  Устгах backup байхгүй ({keep_count}-с цөөн)")


def main():
    """Main функц - command line аргументуудыг боловсруулах"""
    parser = argparse.ArgumentParser(description='Coal LIMS Database Backup')
    parser.add_argument(
        '--db-path',
        default='instance/coal_lims.db',
        help='Database файлын зам (default: instance/coal_lims.db)'
    )
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
        # Backup хийх
        backup_file = backup_database(args.db_path, args.backup_dir)

        # Хуучин backup-уудыг устгах
        if not args.no_cleanup:
            cleanup_old_backups(args.backup_dir, args.keep)

        print("\n✅ Backup бүрэн амжилттай боллоо!")

    except Exception as e:
        print(f"\n❌ Backup хийхэд алдаа гарлаа: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
