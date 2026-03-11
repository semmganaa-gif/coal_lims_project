# config/runtime.py
"""Logging paths and runtime directories."""

import os
from config.base import INSTANCE_DIR


class RuntimeConfig:
    """Log file paths."""
    SECURITY_LOG_FILE = os.path.join(INSTANCE_DIR, 'logs', 'security.log')
    APP_LOG_FILE = os.path.join(INSTANCE_DIR, 'logs', 'app.log')


# Ensure logs directory exists at import time
os.makedirs(os.path.join(INSTANCE_DIR, 'logs'), exist_ok=True)
