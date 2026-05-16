# app/routes/api/workflow_api.py
# -*- coding: utf-8 -*-
"""
Workflow Engine API — configure workflows, query transitions.
"""

from flask import request, jsonify
from flask_login import login_required, current_user
from app.constants import UserRole
from app.utils.decorators import role_required
from flask_babel import gettext as _

from app.bootstrap.extensions import db
from app.routes.api import api_bp
from app.services.workflow_engine import (
    WorkflowEngine,
    get_workflow_config,
    save_workflow_config,
    reset_workflow_config,
    list_workflows,
)

VALID_ROLES = set(UserRole.values())


@api_bp.route("/workflow/list")
@login_required
def workflow_list():
    """List all available workflows."""
    workflows = list_workflows()
    return jsonify(success=True, data=workflows)


@api_bp.route("/workflow/<workflow_name>")
@login_required
def workflow_get(workflow_name):
    """Get full workflow configuration."""
    try:
        config = get_workflow_config(workflow_name)
        return jsonify(success=True, data=config)
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 404


@api_bp.route("/workflow/<workflow_name>/states")
@login_required
def workflow_states(workflow_name):
    """Get workflow states with metadata."""
    try:
        engine = WorkflowEngine(workflow_name)
        states = engine.get_states()
        return jsonify(success=True, data=states)
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 404


@api_bp.route("/workflow/<workflow_name>/transitions")
@login_required
def workflow_transitions(workflow_name):
    """Get available transitions for current user from a given state."""
    from_state = request.args.get("from_state", "")

    try:
        engine = WorkflowEngine(workflow_name)

        if from_state:
            transitions = engine.get_available_transitions(
                from_state, current_user.role
            )
        else:
            transitions = engine.get_transitions()

        return jsonify(success=True, data=transitions)
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 404


@api_bp.route("/workflow/<workflow_name>/can_transition", methods=["POST"])
@login_required
def workflow_can_transition(workflow_name):
    """Check if a specific transition is allowed."""
    data = request.json or {}
    from_state = data.get("from_state", "")
    to_state = data.get("to_state", "")

    if not from_state or not to_state:
        return jsonify(success=False, message=_("from_state, to_state шаардлагатай")), 400

    try:
        engine = WorkflowEngine(workflow_name)
        result = engine.can_transition(
            from_state, to_state,
            user_role=current_user.role,
            context=data.get("context", {}),
        )
        return jsonify(
            success=True,
            data={
                "allowed": result.allowed,
                "reason": result.reason,
                "transition": result.transition,
            },
        )
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 404


@api_bp.route("/workflow/<workflow_name>/save", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN.value)
def workflow_save(workflow_name):
    """Save custom workflow configuration (admin only)."""
    config = request.json
    if not config:
        return jsonify(success=False, message=_("Config шаардлагатай")), 400

    try:
        save_workflow_config(workflow_name, config, current_user.id)
        return jsonify(success=True, message=_("'%(name)s' workflow хадгалагдлаа") % {"name": workflow_name})
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 400


@api_bp.route("/workflow/<workflow_name>/reset", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN.value)
def workflow_reset(workflow_name):
    """Reset workflow to default (admin only)."""
    reset_workflow_config(workflow_name)
    return jsonify(success=True, message=_("'%(name)s' workflow default болгогдлоо") % {"name": workflow_name})


@api_bp.route("/workflow/<workflow_name>/add_state", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN.value)
def workflow_add_state(workflow_name):
    """Add a new state to workflow (admin only)."""
    data = request.json or {}
    state_key = data.get("key", "").strip()
    if not state_key:
        return jsonify(success=False, message=_("State key шаардлагатай")), 400

    try:
        config = get_workflow_config(workflow_name)
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 404

    if state_key in config.get("states", {}):
        return jsonify(success=False, message=_("'%(key)s' state аль хэдийн байна") % {"key": state_key}), 400

    config["states"][state_key] = {
        "label": data.get("label", state_key),
        "label_en": data.get("label_en", state_key),
        "color": data.get("color", "#94a3b8"),
        "icon": data.get("icon", "bi-circle"),
        "order": data.get("order", len(config["states"]) + 1),
    }

    save_workflow_config(workflow_name, config, current_user.id)
    return jsonify(success=True, message=_("'%(key)s' state нэмэгдлээ") % {"key": state_key})


@api_bp.route("/workflow/<workflow_name>/add_transition", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN.value)
def workflow_add_transition(workflow_name):
    """Add a new transition to workflow (admin only)."""
    data = request.json or {}
    from_state = data.get("from", "").strip()
    to_state = data.get("to", "").strip()

    if not from_state or not to_state:
        return jsonify(success=False, message=_("from, to шаардлагатай")), 400

    try:
        config = get_workflow_config(workflow_name)
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 404

    states = config.get("states", {})
    if from_state not in states or to_state not in states:
        return jsonify(success=False, message=_("from/to state олдсонгүй")), 400

    roles = data.get("roles", ["admin"])
    invalid = [r for r in roles if r not in VALID_ROLES]
    if invalid:
        return jsonify(
            success=False,
            message=_("Буруу role: %(invalid)s. Зөвшөөрөгдсөн: %(allowed)s") % {
                "invalid": invalid,
                "allowed": sorted(VALID_ROLES),
            },
        ), 400

    config.setdefault("transitions", []).append({
        "from": from_state,
        "to": to_state,
        "label": data.get("label", f"{from_state} → {to_state}"),
        "label_en": data.get("label_en", f"{from_state} → {to_state}"),
        "roles": roles,
        "conditions": data.get("conditions", []),
    })

    save_workflow_config(workflow_name, config, current_user.id)
    return jsonify(success=True, message=_("'%(from)s' → '%(to)s' transition нэмэгдлээ") % {"from": from_state, "to": to_state})


@api_bp.route("/workflow/<workflow_name>/update_state", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN.value)
def workflow_update_state(workflow_name):
    """Update an existing state (admin only)."""
    data = request.json or {}
    state_key = data.get("key", "").strip()
    if not state_key:
        return jsonify(success=False, message=_("State key шаардлагатай")), 400

    try:
        config = get_workflow_config(workflow_name)
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 404

    if state_key not in config.get("states", {}):
        return jsonify(success=False, message=_("'%(key)s' state олдсонгүй") % {"key": state_key}), 404

    state = config["states"][state_key]
    if "label" in data:
        state["label"] = data["label"]
    if "label_en" in data:
        state["label_en"] = data["label_en"]
    if "color" in data:
        state["color"] = data["color"]
    if "icon" in data:
        state["icon"] = data["icon"]
    if "order" in data:
        state["order"] = data["order"]

    save_workflow_config(workflow_name, config, current_user.id)
    return jsonify(success=True, message=_("'%(key)s' state шинэчлэгдлээ") % {"key": state_key})


@api_bp.route("/workflow/<workflow_name>/delete_state", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN.value)
def workflow_delete_state(workflow_name):
    """Delete a state and its transitions (admin only)."""
    data = request.json or {}
    state_key = data.get("key", "").strip()
    if not state_key:
        return jsonify(success=False, message=_("State key шаардлагатай")), 400

    try:
        config = get_workflow_config(workflow_name)
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 404

    if state_key not in config.get("states", {}):
        return jsonify(success=False, message=_("'%(key)s' state олдсонгүй") % {"key": state_key}), 404

    if state_key == config.get("initial_state"):
        return jsonify(success=False, message=_("Initial state устгаж болохгүй")), 400

    del config["states"][state_key]
    config["transitions"] = [
        t for t in config.get("transitions", [])
        if t["from"] != state_key and t["to"] != state_key
    ]
    if state_key in config.get("final_states", []):
        config["final_states"].remove(state_key)

    save_workflow_config(workflow_name, config, current_user.id)
    return jsonify(success=True, message=_("'%(key)s' state устгагдлаа") % {"key": state_key})


@api_bp.route("/workflow/<workflow_name>/update_transition", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN.value)
def workflow_update_transition(workflow_name):
    """Update an existing transition (admin only)."""
    data = request.json or {}
    idx = data.get("index")
    if idx is None:
        return jsonify(success=False, message=_("Transition index шаардлагатай")), 400

    try:
        config = get_workflow_config(workflow_name)
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 404

    transitions = config.get("transitions", [])
    if idx < 0 or idx >= len(transitions):
        return jsonify(success=False, message=_("Transition index буруу")), 400

    t = transitions[idx]
    if "label" in data:
        t["label"] = data["label"]
    if "label_en" in data:
        t["label_en"] = data["label_en"]
    if "roles" in data:
        invalid = [r for r in data["roles"] if r not in VALID_ROLES]
        if invalid:
            return jsonify(
            success=False,
            message=_("Буруу role: %(invalid)s. Зөвшөөрөгдсөн: %(allowed)s") % {
                "invalid": invalid,
                "allowed": sorted(VALID_ROLES),
            },
        ), 400
        t["roles"] = data["roles"]
    if "conditions" in data:
        t["conditions"] = data["conditions"]

    save_workflow_config(workflow_name, config, current_user.id)
    return jsonify(success=True, message=_("Transition шинэчлэгдлээ"))


@api_bp.route("/workflow/<workflow_name>/delete_transition", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN.value)
def workflow_delete_transition(workflow_name):
    """Delete a transition by index (admin only)."""
    data = request.json or {}
    idx = data.get("index")
    if idx is None:
        return jsonify(success=False, message=_("Transition index шаардлагатай")), 400

    try:
        config = get_workflow_config(workflow_name)
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 404

    transitions = config.get("transitions", [])
    if idx < 0 or idx >= len(transitions):
        return jsonify(success=False, message=_("Transition index буруу")), 400

    removed = transitions.pop(idx)
    save_workflow_config(workflow_name, config, current_user.id)
    return jsonify(success=True, message=_("'%(from)s' → '%(to)s' transition устгагдлаа") % {"from": removed['from'], "to": removed['to']})


@api_bp.route("/workflow/analysis_result/actions/<int:result_id>")
@login_required
def workflow_result_actions(result_id):
    """Get available workflow actions for a specific analysis result."""
    from app.models import AnalysisResult

    res = db.session.get(AnalysisResult, result_id)
    if not res:
        return jsonify({"success": False, "message": "Not found"}), 404

    engine = WorkflowEngine("analysis_result")
    user_role = getattr(current_user, "role", None) or ""
    transitions = engine.get_available_transitions(res.status, user_role)

    state_info = engine.get_state_info(res.status)

    return jsonify({
        "success": True,
        "data": {
            "current_state": res.status,
            "state_info": state_info,
            "actions": [
                {
                    "to": t["to"],
                    "label": t.get("label", t["to"]),
                    "label_en": t.get("label_en", t["to"]),
                    "requires_comment": "require_comment" in t.get("conditions", []),
                }
                for t in transitions
            ],
        },
    })
