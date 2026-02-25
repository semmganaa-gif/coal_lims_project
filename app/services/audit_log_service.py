"""
General audit log service (non-analysis entities).

This module only provides log_action for generic audit entries.
Analysis-specific audit logging lives in app/services/analysis_audit.py.
"""

from __future__ import annotations

import logging
from typing import Optional

from flask_login import current_user

logger = logging.getLogger(__name__)


def log_action(
    action: str,
    entity_type: str,
    entity_id: int,
    details: Optional[str] = None,
) -> None:
    """
    General audit log action for non-analysis entities.
    Uses logger to record the action.
    """
    try:
        user_id = current_user.id if getattr(current_user, "is_authenticated", False) else -1
        logger.info(
            f"[AUDIT] action={action} entity_type={entity_type} entity_id={entity_id} "
            f"user_id={user_id} details={details}"
        )
    except Exception as e:
        logger.warning(f"log_action failed: {e}")
