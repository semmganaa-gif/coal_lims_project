# app/tasks/instrument_tasks.py
# -*- coding: utf-8 -*-
"""
Celery tasks for instrument file watching and auto-import.

Uses watchdog for filesystem monitoring, or polling fallback.
"""

import os
import logging

from app.bootstrap.celery_app import celery_app

logger = logging.getLogger(__name__)

# Default watch directories per instrument type
DEFAULT_WATCH_DIRS = {
    "tga": "instrument_data/tga",
    "bomb_cal": "instrument_data/bomb_cal",
    "elemental": "instrument_data/elemental",
    "generic_csv": "instrument_data/generic_csv",
}


@celery_app.task(bind=True, name="app.tasks.instrument_tasks.scan_instrument_dirs")
def scan_instrument_dirs(self):
    """
    Periodic task: scan instrument directories for new files and import them.
    Runs every 60 seconds via Celery Beat.
    """
    from flask import current_app
    from app.services.instrument_service import import_instrument_file

    watch_dirs = current_app.config.get("INSTRUMENT_WATCH_DIRS", DEFAULT_WATCH_DIRS)
    base_path = current_app.config.get("INSTRUMENT_BASE_PATH", "")
    processed_dir = current_app.config.get("INSTRUMENT_PROCESSED_DIR", "instrument_data/_processed")

    total_imported = 0

    for instrument_type, rel_dir in watch_dirs.items():
        watch_path = os.path.join(base_path, rel_dir) if base_path else rel_dir

        if not os.path.isdir(watch_path):
            continue

        for filename in os.listdir(watch_path):
            filepath = os.path.join(watch_path, filename)
            if not os.path.isfile(filepath):
                continue

            # Skip hidden files and temp files
            if filename.startswith(".") or filename.startswith("~"):
                continue

            try:
                count = import_instrument_file(filepath, instrument_type)
                total_imported += count
                logger.info(f"Imported {count} readings from {filepath}")

                # Move to processed directory
                _move_to_processed(filepath, processed_dir, instrument_type)

            except ValueError as e:
                # Duplicate file or parse error — move to processed to avoid retry
                logger.warning(f"Skipping {filepath}: {e}")
                _move_to_processed(filepath, processed_dir, instrument_type)
            except Exception:
                logger.exception(f"Error processing {filepath}")

    return {"imported": total_imported}


def _move_to_processed(filepath: str, processed_dir: str, instrument_type: str):
    """Move processed file to archive directory."""
    dest_dir = os.path.join(processed_dir, instrument_type)
    os.makedirs(dest_dir, exist_ok=True)

    filename = os.path.basename(filepath)
    dest_path = os.path.join(dest_dir, filename)

    # Handle name collision
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
            counter += 1

    try:
        os.rename(filepath, dest_path)
    except OSError:
        # Cross-device move fallback
        import shutil
        shutil.move(filepath, dest_path)
