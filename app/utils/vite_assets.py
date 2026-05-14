"""Vite manifest helper — hashed asset URL resolution for Flask templates."""

import json
from functools import lru_cache
from pathlib import Path

from flask import current_app, url_for
from markupsafe import Markup


_MANIFEST_PATH = Path("static") / "dist" / ".vite" / "manifest.json"


@lru_cache(maxsize=1)
def _load_manifest_cached(manifest_mtime: float, app_root: str) -> dict:
    """Cache manifest read by mtime so dev rebuilds reflect immediately."""
    manifest_file = Path(app_root) / _MANIFEST_PATH
    with manifest_file.open(encoding="utf-8") as f:
        return json.load(f)


def _load_manifest() -> dict:
    manifest_file = Path(current_app.root_path) / _MANIFEST_PATH
    if not manifest_file.exists():
        return {}
    return _load_manifest_cached(manifest_file.stat().st_mtime, current_app.root_path)


def vite_asset(entry: str) -> str:
    """Resolve a Vite entry (e.g. 'src/styles.css') to a hashed static URL.

    Falls back to the entry path if manifest is missing — surfaces the misconfig
    to the developer without crashing the page.
    """
    manifest = _load_manifest()
    entry_info = manifest.get(entry)
    if not entry_info:
        current_app.logger.warning("Vite manifest missing entry: %s", entry)
        return url_for("static", filename=f"dist/{entry}")
    return url_for("static", filename=f"dist/{entry_info['file']}")


def vite_css_tag(entry: str) -> Markup:
    """Render a CSP-nonce-aware <link> tag for a CSS entry."""
    from flask import g
    nonce = getattr(g, "csp_nonce", "")
    href = vite_asset(entry)
    nonce_attr = f' nonce="{nonce}"' if nonce else ""
    return Markup(f'<link rel="stylesheet" href="{href}"{nonce_attr}>')


def vite_js_tag(entry: str) -> Markup:
    """Render a CSP-nonce-aware <script type=module> tag for a JS entry."""
    from flask import g
    nonce = getattr(g, "csp_nonce", "")
    src = vite_asset(entry)
    nonce_attr = f' nonce="{nonce}"' if nonce else ""
    return Markup(f'<script type="module" src="{src}"{nonce_attr}></script>')
