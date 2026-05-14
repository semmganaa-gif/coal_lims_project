# app/services/workflow_engine.py
# -*- coding: utf-8 -*-
"""
Configurable Workflow Engine.

Тохируулж болохуйц ажлын урсгал (state machine).
Admin-аас states, transitions, conditions тохируулна.
SystemSetting (category='workflow') дээр JSON хадгална.

Workflow config JSON формат:
{
    "name": "analysis_result",
    "description": "Шинжилгээний үр дүнгийн workflow",
    "states": {
        "pending_review": {"label": "Хянагдаж байна", "color": "#f59e0b", "order": 1},
        "approved":       {"label": "Батлагдсан",     "color": "#22c55e", "order": 2},
        "rejected":       {"label": "Татгалзсан",     "color": "#ef4444", "order": 3},
        "reanalysis":     {"label": "Дахин шинжлэх",  "color": "#8b5cf6", "order": 4}
    },
    "initial_state": "pending_review",
    "final_states": ["approved"],
    "transitions": [
        {
            "from": "pending_review", "to": "approved",
            "label": "Батлах", "roles": ["senior", "admin", "manager"],
            "conditions": []
        },
        {
            "from": "pending_review", "to": "rejected",
            "label": "Татгалзах", "roles": ["senior", "admin", "manager"],
            "conditions": ["require_comment"]
        },
        ...
    ],
    "hooks": {
        "on_approve": ["invalidate_cache", "log_audit"],
        "on_reject":  ["notify_analyst", "log_audit"]
    }
}
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from app.bootstrap.extensions import db
from app.models.settings import SystemSetting

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────
# Default workflow configurations
# ──────────────────────────────────────────

DEFAULT_WORKFLOWS = {
    "analysis_result": {
        "name": "analysis_result",
        "description": "Шинжилгээний үр дүнгийн workflow",
        "entity": "AnalysisResult",
        "states": {
            "pending_review": {
                "label": "Хянагдаж байна",
                "label_en": "Pending Review",
                "color": "#f59e0b",
                "icon": "bi-clock",
                "order": 1,
            },
            "approved": {
                "label": "Батлагдсан",
                "label_en": "Approved",
                "color": "#22c55e",
                "icon": "bi-check-circle",
                "order": 2,
            },
            "rejected": {
                "label": "Татгалзсан",
                "label_en": "Rejected",
                "color": "#ef4444",
                "icon": "bi-x-circle",
                "order": 3,
            },
            "reanalysis": {
                "label": "Дахин шинжлэх",
                "label_en": "Reanalysis",
                "color": "#8b5cf6",
                "icon": "bi-arrow-repeat",
                "order": 4,
            },
        },
        "initial_state": "pending_review",
        "final_states": ["approved"],
        "transitions": [
            {
                "from": "pending_review",
                "to": "approved",
                "label": "Батлах",
                "label_en": "Approve",
                "roles": ["senior", "admin", "manager"],
                "conditions": [],
            },
            {
                "from": "pending_review",
                "to": "rejected",
                "label": "Татгалзах",
                "label_en": "Reject",
                "roles": ["senior", "admin", "manager"],
                "conditions": ["require_comment"],
            },
            {
                "from": "rejected",
                "to": "pending_review",
                "label": "Дахин илгээх",
                "label_en": "Resubmit",
                "roles": ["chemist", "senior", "admin", "manager"],
                "conditions": [],
            },
            {
                "from": "rejected",
                "to": "approved",
                "label": "Батлах (override)",
                "label_en": "Approve (override)",
                "roles": ["admin", "manager"],
                "conditions": ["require_comment"],
            },
            {
                "from": "pending_review",
                "to": "reanalysis",
                "label": "Дахин шинжлэх",
                "label_en": "Request Reanalysis",
                "roles": ["senior", "admin", "manager"],
                "conditions": ["require_comment"],
            },
            {
                "from": "reanalysis",
                "to": "pending_review",
                "label": "Илгээх",
                "label_en": "Submit",
                "roles": ["chemist", "senior", "admin", "manager"],
                "conditions": [],
            },
            {
                "from": "approved",
                "to": "pending_review",
                "label": "Буцаах",
                "label_en": "Return to Review",
                "roles": ["senior", "admin", "manager"],
                "conditions": [],
            },
        ],
        "hooks": {
            "on_enter_approved": ["invalidate_cache", "log_audit", "check_sample_complete"],
            "on_enter_rejected": ["log_audit", "notify_analyst"],
            "on_enter_reanalysis": ["log_audit"],
        },
    },
    "sample": {
        "name": "sample",
        "description": "Дээжийн workflow",
        "entity": "Sample",
        "states": {
            "new": {
                "label": "Шинэ",
                "label_en": "New",
                "color": "#3b82f6",
                "icon": "bi-plus-circle",
                "order": 1,
            },
            "in_progress": {
                "label": "Хийгдэж байна",
                "label_en": "In Progress",
                "color": "#f59e0b",
                "icon": "bi-gear",
                "order": 2,
            },
            "analysis": {
                "label": "Шинжилгээнд",
                "label_en": "In Analysis",
                "color": "#8b5cf6",
                "icon": "bi-flask",
                "order": 3,
            },
            "completed": {
                "label": "Дууссан",
                "label_en": "Completed",
                "color": "#22c55e",
                "icon": "bi-check-circle",
                "order": 4,
            },
            "archived": {
                "label": "Архивлагдсан",
                "label_en": "Archived",
                "color": "#94a3b8",
                "icon": "bi-archive",
                "order": 5,
            },
        },
        "initial_state": "new",
        "final_states": ["completed", "archived"],
        "transitions": [
            {
                "from": "new",
                "to": "in_progress",
                "label": "Эхлэх",
                "label_en": "Start",
                "roles": ["chemist", "senior", "admin", "manager"],
                "conditions": [],
            },
            {
                "from": "in_progress",
                "to": "analysis",
                "label": "Шинжилгээнд оруулах",
                "label_en": "Begin Analysis",
                "roles": ["chemist", "senior", "admin", "manager"],
                "conditions": [],
            },
            {
                "from": "analysis",
                "to": "completed",
                "label": "Дуусгах",
                "label_en": "Complete",
                "roles": ["senior", "admin", "manager"],
                "conditions": ["all_results_approved"],
            },
            {
                "from": "completed",
                "to": "archived",
                "label": "Архивлах",
                "label_en": "Archive",
                "roles": ["admin", "manager"],
                "conditions": [],
            },
            {
                "from": "archived",
                "to": "completed",
                "label": "Сэргээх",
                "label_en": "Restore",
                "roles": ["admin"],
                "conditions": [],
            },
            {
                "from": "new",
                "to": "analysis",
                "label": "Шууд шинжлэх",
                "label_en": "Direct Analysis",
                "roles": ["chemist", "senior", "admin", "manager"],
                "conditions": [],
            },
        ],
        "hooks": {
            "on_enter_completed": ["log_audit", "mark_sla_completed"],
            "on_enter_archived": ["log_audit"],
        },
    },
}


@dataclass
class TransitionResult:
    """Transition validation result."""
    allowed: bool
    reason: str = ""
    transition: dict = field(default_factory=dict)


class WorkflowEngine:
    """
    Configurable state machine for entity workflows.

    Usage:
        engine = WorkflowEngine("analysis_result")
        result = engine.can_transition("pending_review", "approved", user_role="senior")
        if result.allowed:
            engine.execute_transition(entity, "approved", user)
    """

    def __init__(self, workflow_name: str):
        self.workflow_name = workflow_name
        self._config = None

    @property
    def config(self) -> dict:
        """Load workflow config (DB override > default)."""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> dict:
        """Load from SystemSetting, fallback to defaults."""
        setting = SystemSetting.query.filter_by(
            category="workflow",
            key=self.workflow_name,
            is_active=True,
        ).first()

        if setting:
            try:
                return json.loads(setting.value)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid workflow config for '{self.workflow_name}', using default")

        if self.workflow_name in DEFAULT_WORKFLOWS:
            return DEFAULT_WORKFLOWS[self.workflow_name]

        raise ValueError(f"Unknown workflow: {self.workflow_name}")

    def reload(self):
        """Force reload config from DB."""
        self._config = None

    # ──────────────────────────────────
    # State queries
    # ──────────────────────────────────

    def get_states(self) -> dict:
        """Get all states with metadata."""
        return self.config.get("states", {})

    def get_state_info(self, state: str) -> Optional[dict]:
        """Get state metadata (label, color, icon)."""
        return self.config.get("states", {}).get(state)

    def get_initial_state(self) -> str:
        return self.config.get("initial_state", "")

    def get_final_states(self) -> list[str]:
        return self.config.get("final_states", [])

    def is_final_state(self, state: str) -> bool:
        return state in self.get_final_states()

    # ──────────────────────────────────
    # Transition queries
    # ──────────────────────────────────

    def get_transitions(self, from_state: str = None) -> list[dict]:
        """Get all transitions, optionally filtered by from_state."""
        transitions = self.config.get("transitions", [])
        if from_state is not None:
            return [t for t in transitions if t["from"] == from_state]
        return transitions

    def get_available_transitions(self, from_state: str,
                                  user_role: str) -> list[dict]:
        """Get transitions available to a user from current state."""
        result = []
        for t in self.get_transitions(from_state):
            if user_role in t.get("roles", []):
                result.append(t)
        return result

    def can_transition(self, from_state: str, to_state: str,
                       user_role: str = None,
                       context: dict = None) -> TransitionResult:
        """
        Check if transition is allowed.

        Args:
            from_state: Current state
            to_state: Target state
            user_role: User's role string
            context: Additional context for condition evaluation

        Returns:
            TransitionResult with allowed flag and reason
        """
        transitions = self.get_transitions(from_state)

        # Find matching transition
        matching = [t for t in transitions if t["to"] == to_state]

        if not matching:
            return TransitionResult(
                allowed=False,
                reason=f"'{from_state}' → '{to_state}' шилжилт тодорхойлогдоогүй"
            )

        transition = matching[0]

        # Check role
        if user_role and user_role not in transition.get("roles", []):
            return TransitionResult(
                allowed=False,
                reason=f"'{user_role}' эрх энэ шилжилтэд хүрэлцэхгүй. "
                       f"Шаардлагатай: {transition.get('roles', [])}"
            )

        # Check conditions
        conditions = transition.get("conditions", [])
        context = context or {}

        for condition in conditions:
            ok, msg = self._evaluate_condition(condition, context)
            if not ok:
                return TransitionResult(
                    allowed=False,
                    reason=msg,
                    transition=transition,
                )

        return TransitionResult(allowed=True, transition=transition)

    def _evaluate_condition(self, condition: str,
                            context: dict) -> tuple[bool, str]:
        """Evaluate a transition condition."""
        if condition == "require_comment":
            comment = context.get("comment", "").strip()
            if not comment:
                return False, "Тайлбар бичих шаардлагатай"
            return True, ""

        elif condition == "all_results_approved":
            # Check that all analysis results for the sample are approved
            all_approved = context.get("all_results_approved", False)
            if not all_approved:
                return False, "Бүх шинжилгээний үр дүн батлагдсан байх шаардлагатай"
            return True, ""

        elif condition == "require_reanalysis_reason":
            reason = context.get("reanalysis_reason", "").strip()
            if not reason:
                return False, "Дахин шинжилгээний шалтгаан бичих шаардлагатай"
            return True, ""

        elif condition.startswith("min_results:"):
            # e.g., "min_results:2"
            try:
                min_count = int(condition.split(":")[1])
            except (IndexError, ValueError):
                min_count = 1
            result_count = context.get("result_count", 0)
            if result_count < min_count:
                return False, f"Хамгийн багадаа {min_count} үр дүн шаардлагатай"
            return True, ""

        # Unknown condition — allow by default (extensible)
        logger.warning(f"Unknown workflow condition: {condition}")
        return True, ""

    def get_hooks(self, state: str, event: str = "on_enter") -> list[str]:
        """Get hook names for a state event."""
        hooks = self.config.get("hooks", {})
        key = f"{event}_{state}"
        return hooks.get(key, [])

    def execute_hooks(self, new_state: str, context: dict = None):
        """Execute hooks for entering a state."""
        hook_names = self.get_hooks(new_state)
        context = context or {}
        for hook_name in hook_names:
            try:
                _run_hook(hook_name, context)
            except Exception:
                logger.exception(f"Hook '{hook_name}' failed for state '{new_state}'")


# ──────────────────────────────────────────
# Hook execution
# ──────────────────────────────────────────

def _run_hook(name: str, context: dict):
    """Execute a named hook."""
    if name == "invalidate_cache":
        from app.bootstrap.extensions import cache
        cache.delete('kpi_summary_ahlah')
        cache.delete('ahlah_stats')
    elif name == "log_audit":
        from app.utils.audit import log_audit
        log_audit(
            action=f"workflow_{context.get('workflow_name', '')}_{context.get('to_state', '')}",
            resource_type=context.get('entity_type', ''),
            resource_id=context.get('entity_id', 0),
            details={
                'from_state': context.get('from_state', ''),
                'to_state': context.get('to_state', ''),
                'comment': context.get('comment', ''),
            },
        )
    elif name == "check_sample_complete":
        _hook_check_sample_complete(context)
    elif name == "notify_analyst":
        logger.info(
            "Notification: workflow transition %s → %s for %s #%s",
            context.get('from_state'), context.get('to_state'),
            context.get('entity_type'), context.get('entity_id'),
        )
    elif name == "mark_sla_completed":
        sample = context.get('entity')
        if sample:
            from app.services.sla_service import mark_completed
            mark_completed(sample)
    else:
        logger.warning(f"Unknown hook: {name}")


def _hook_check_sample_complete(context: dict):
    """Check if all analysis results for a sample are approved."""
    from app.models import AnalysisResult
    sample_id = context.get('sample_id')
    if not sample_id:
        return
    pending = AnalysisResult.query.filter(
        AnalysisResult.sample_id == sample_id,
        AnalysisResult.status != 'approved',
    ).count()
    if pending == 0:
        from app.models import Sample
        sample = db.session.get(Sample, sample_id)
        if sample and sample.status not in ('completed', 'archived'):
            sample.status = 'completed'
            from app.services.sla_service import mark_completed
            mark_completed(sample)
            logger.info(f"Sample #{sample_id} auto-completed (all results approved)")


# ──────────────────────────────────────────
# Configuration management
# ──────────────────────────────────────────

def get_workflow_config(workflow_name: str) -> dict:
    """Get workflow configuration."""
    engine = WorkflowEngine(workflow_name)
    return engine.config


def save_workflow_config(workflow_name: str, config: dict,
                         user_id: int = None) -> bool:
    """
    Save workflow configuration to SystemSetting.

    Validates config structure before saving.
    """
    # Validate required fields
    required = {"name", "states", "initial_state", "transitions"}
    if not required.issubset(set(config.keys())):
        raise ValueError(f"Config-д шаардлагатай: {required}")

    # Validate initial_state is in states
    if config["initial_state"] not in config["states"]:
        raise ValueError(f"initial_state '{config['initial_state']}' states-д олдсонгүй")

    # Validate transitions reference valid states
    state_names = set(config["states"].keys())
    for t in config.get("transitions", []):
        if t.get("from") not in state_names:
            raise ValueError(f"Transition 'from' state '{t['from']}' олдсонгүй")
        if t.get("to") not in state_names:
            raise ValueError(f"Transition 'to' state '{t['to']}' олдсонгүй")

    # Upsert
    setting = SystemSetting.query.filter_by(
        category="workflow",
        key=workflow_name,
    ).first()

    if setting:
        setting.value = json.dumps(config, ensure_ascii=False)
        setting.is_active = True
        setting.updated_by_id = user_id
    else:
        setting = SystemSetting(
            category="workflow",
            key=workflow_name,
            value=json.dumps(config, ensure_ascii=False),
            description=config.get("description", ""),
            is_active=True,
            updated_by_id=user_id,
        )
        db.session.add(setting)

    db.session.commit()
    return True


def reset_workflow_config(workflow_name: str) -> bool:
    """Reset workflow to default by deactivating custom config."""
    setting = SystemSetting.query.filter_by(
        category="workflow",
        key=workflow_name,
    ).first()

    if setting:
        setting.is_active = False
        db.session.commit()
    return True


def list_workflows() -> list[dict]:
    """List all available workflows with status."""
    result = []
    for name, default_config in DEFAULT_WORKFLOWS.items():
        custom = SystemSetting.query.filter_by(
            category="workflow", key=name, is_active=True
        ).first()

        result.append({
            "name": name,
            "description": default_config.get("description", ""),
            "entity": default_config.get("entity", ""),
            "is_customized": custom is not None,
            "state_count": len(default_config.get("states", {})),
            "transition_count": len(default_config.get("transitions", [])),
        })

    return result
