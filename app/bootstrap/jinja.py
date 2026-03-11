# app/bootstrap/jinja.py
"""Jinja2 template filters and context processors."""

import json
from markupsafe import Markup
from app.utils.datetime import now_local


def init_jinja(app):
    """Register Jinja2 filters and context processor."""

    # ---- Filter: loads (parse JSON strings) ----
    def jinja_loads_filter(value):
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            s = value.strip()
            if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                try:
                    return json.loads(s)
                except (json.JSONDecodeError, ValueError):
                    return {} if s.startswith("{") else []
        return {}

    app.jinja_env.filters["loads"] = jinja_loads_filter

    # ---- Filter: fmt_result (centralized precision) ----
    from app.config.display_precision import format_result as format_result_centralized

    app.add_template_filter(
        lambda v, analysis_code=None: format_result_centralized(v, analysis_code),
        name="fmt_result"
    )

    # ---- Filter: fmt_code (subscript analysis codes) ----
    from app.constants import ANALYSIS_CODE_SUBSCRIPTS

    def fmt_code(code: str | None) -> Markup:
        if not code:
            return Markup("")
        c = str(code).strip()
        lookup = c.lower().replace(" ", "")
        sub = ANALYSIS_CODE_SUBSCRIPTS.get(lookup)
        if sub:
            prefix, subscript = sub
            if subscript:
                return Markup(f'{prefix}<sub>{subscript}</sub>')
            return Markup(prefix)
        # Fallback: comma-based subscript (e.g. "St,d" → S<sub>t,d</sub>)
        if "," in c:
            parts = c.split(",", 1)
            prefix_part = parts[0]
            sub_part = parts[1]
            i = len(prefix_part)
            for j in range(len(prefix_part) - 1, 0, -1):
                if prefix_part[j].islower():
                    i = j
                else:
                    break
            if i < len(prefix_part):
                real_prefix = prefix_part[:i]
                sub_start = prefix_part[i:]
                return Markup(f'{real_prefix}<sub>{sub_start},{sub_part}</sub>')
            return Markup(f'{prefix_part}<sub>{sub_part}</sub>')
        return Markup(c)

    app.add_template_filter(fmt_code, name="fmt_code")

    # ---- Context processor ----
    @app.context_processor
    def inject_utility_functions():
        from app.utils.repeatability_loader import load_limit_rules
        from app.labs import LAB_TYPES
        from app.bootstrap.i18n import get_locale
        return dict(
            now_local=now_local,
            LIMS_LIMIT_RULES=load_limit_rules(),
            LAB_TYPES=LAB_TYPES,
            get_locale=get_locale,
        )
