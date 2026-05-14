"""Migrate inline event handlers (`onclick="fn(args)"` etc.) to CSP-compatible
data-action attributes. Companion to csp_handlers.js dispatcher.

Strategy:
  - For SIMPLE function calls `fn(arg1, arg2, ...)`:
      * Generate kebab-case action name from fn name
      * Encode positional args as data-arg-N attributes
      * Store original fn name in data-action so existing JS can be reused
        via the LIMS_ACTIONS fallback (which looks up window[action_name])
        OR via explicit registration in csp_handlers.js / per-feature modules.

  - For known patterns that csp_handlers.js already handles:
      * `this.form.submit()` → data-autosubmit
      * `return confirm("X")` → data-confirm="X"
      * `location.reload()` → data-action="reload"
      * `history.back()` → data-action="back"
      * `window.print()` → data-action="print"

  - For COMPLEX inline JS (multi-statement, ternary, this.foo = bar):
      * Skip and report for manual review.

Modes:
  --report  Dry-run; print which handlers would migrate and which need manual.
  --apply   Modify templates in place.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "app" / "templates"

# Match `onevent="..."` allowing nested Jinja `{{ ... }}` (which may contain
# unbalanced quotes that would otherwise terminate the HTML attribute prematurely).
HANDLER_RE = re.compile(
    r'''(\s)on([a-z]+)\s*=\s*"((?:[^"{]|\{(?!\{)|\{\{(?:[^}]|\}(?!\}))*\}\})*)"'''
)

SIMPLE_CALL_RE = re.compile(r"^\s*([A-Za-z_][\w]*)\s*\(\s*(.*?)\s*\)\s*;?\s*$")
RETURN_CONFIRM_RE = re.compile(r"^\s*return\s+confirm\((['\"])(?P<msg>.+?)\1\)\s*;?\s*$")
THIS_FORM_SUBMIT_RE = re.compile(r"^\s*(?:this|this\.form)\.submit\(\s*\)\s*;?\s*$")
LOCATION_RELOAD_RE = re.compile(r"^\s*location\.reload\(\s*\)\s*;?\s*$")
HISTORY_BACK_RE = re.compile(r"^\s*history\.back\(\s*\)\s*;?\s*$")
WINDOW_PRINT_RE = re.compile(r"^\s*window\.print\(\s*\)\s*;?\s*$")
EVENT_STOP_PROP_RE = re.compile(r"^\s*event\.stopPropagation\(\s*\)\s*;?\s*$")
EVENT_PREVENT_DEFAULT_RE = re.compile(r"^\s*event\.preventDefault\(\s*\)\s*;?\s*$")
THIS_HIDE_RE = re.compile(r"^\s*this\.style\.display\s*=\s*['\"]none['\"]\s*;?\s*$")
THIS_UPPERCASE_RE = re.compile(r"^\s*this\.value\s*=\s*this\.value\.toUpperCase\(\s*\)\s*;?\s*$")
WINDOW_LOCATION_RE = re.compile(r"""^\s*window\.location\s*=\s*['"](?P<url>.+?)['"]\s*;?\s*$""")
THIS_NEXT_TOGGLE_RE = re.compile(r"""^\s*this\.nextElementSibling\.classList\.toggle\(['"](?P<cls>[^'"]+)['"]\)\s*;?\s*$""")
THIS_CLOSEST_REMOVE_RE = re.compile(r"""^\s*this\.closest\(['"](?P<sel>[^'"]+)['"]\)\.remove\(\s*\)\s*;?\s*$""")
GETELEM_HIDE_RE = re.compile(r"""^\s*document\.getElementById\(['"](?P<id>[^'"]+)['"]\)\.style\.display\s*=\s*['"]none['"]\s*;?\s*$""")
JQUERY_TOGGLE_RE = re.compile(r"""^\s*\$\(['"](?P<sel>[^'"]+)['"]\)\.toggle\(\s*\)\s*;?\s*$""")


def parse_args(args_str: str) -> list[str] | None:
    """Parse a simple `arg1, arg2, ...` list. Returns list of args (with quotes
    stripped from string literals). Returns None if unparseable."""
    if not args_str.strip():
        return []
    # Try simple comma split, respecting quoted strings.
    args: list[str] = []
    current = []
    depth = 0
    quote = None
    for ch in args_str:
        if quote:
            if ch == quote:
                quote = None
            current.append(ch)
        elif ch in ('"', "'"):
            quote = ch
            current.append(ch)
        elif ch in "([{":
            depth += 1
            current.append(ch)
        elif ch in ")]}":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        args.append("".join(current).strip())

    # Validate args are simple literals, Jinja interpolation, or identifiers
    cleaned: list[str] = []
    for arg in args:
        a = arg.strip()
        if not a:
            continue
        # String literal — strip quotes, handle escape
        if (a.startswith('"') and a.endswith('"')) or (a.startswith("'") and a.endswith("'")):
            cleaned.append(a[1:-1])
        # Numeric literal
        elif re.match(r"^-?\d+(\.\d+)?$", a):
            cleaned.append(a)
        # Boolean / null / this
        elif a in ("true", "false", "null", "this"):
            cleaned.append(a)
        # Jinja interpolation — passes through to data attribute as-is
        elif re.match(r"^\{\{[^}]+\}\}$", a):
            cleaned.append(a)
        else:
            return None  # Variable reference, expression — too complex for auto-migration
    return cleaned


def kebab(name: str) -> str:
    """fooBarBaz → foo-bar-baz; setQuickTime → set-quick-time"""
    s = re.sub(r"([a-z\d])([A-Z])", r"\1-\2", name)
    return s.lower()


def classify_and_convert(event: str, value: str) -> tuple[str, str | None]:
    """Returns (status, replacement_attrs) where replacement_attrs is the
    string to substitute for the original `onevent="value"` (without leading
    whitespace), or None if cannot migrate.

    status one of:
      'migrated' — replacement_attrs is set
      'skip_complex' — manual review needed
      'skip_unknown' — unrecognized pattern
    """
    v = value.strip()

    # Pattern: return confirm("X")
    m = RETURN_CONFIRM_RE.match(v)
    if m:
        msg = m.group("msg")
        # If message contains Jinja interpolation with literal `"`, use single-
        # quote attribute to avoid &quot; escaping (which Jinja can't parse).
        has_jinja_with_quotes = "{{" in msg and '"' in msg
        attr = "data-confirm" if event == "submit" else "data-click-confirm" if event == "click" else None
        if attr is None:
            return ("skip_complex", None)
        if has_jinja_with_quotes:
            return ("migrated", f"{attr}='{msg}'")
        # No Jinja, safe to escape
        msg = msg.replace('"', '&quot;')
        return ("migrated", f'{attr}="{msg}"')

    # this.form.submit() / this.submit()
    if THIS_FORM_SUBMIT_RE.match(v):
        if event in ("change", "input"):
            return ("migrated", "data-autosubmit")
        return ("skip_complex", None)

    if LOCATION_RELOAD_RE.match(v):
        return ("migrated", 'data-action="reload"')
    if HISTORY_BACK_RE.match(v):
        return ("migrated", 'data-action="back"')
    if WINDOW_PRINT_RE.match(v):
        return ("migrated", 'data-action="print"')
    if EVENT_STOP_PROP_RE.match(v):
        return ("migrated", 'data-action="stop-propagation"')
    if EVENT_PREVENT_DEFAULT_RE.match(v):
        return ("migrated", 'data-action="prevent-default"')
    if event == "error" and THIS_HIDE_RE.match(v):
        return ("migrated", 'data-error-action="hide-self"')
    if event == "input" and THIS_UPPERCASE_RE.match(v):
        return ("migrated", 'data-input-action="uppercase"')
    m = WINDOW_LOCATION_RE.match(v)
    if m:
        url = m.group("url").replace('"', '&quot;')
        return ("migrated", f'data-action="navigate" data-href="{url}"')

    m = THIS_NEXT_TOGGLE_RE.match(v)
    if m:
        cls = m.group("cls")
        return ("migrated", f'data-action="toggle-next-class" data-class-name="{cls}"')

    m = THIS_CLOSEST_REMOVE_RE.match(v)
    if m:
        sel = m.group("sel").replace('"', '&quot;')
        return ("migrated", f'data-action="remove-closest" data-selector="{sel}"')

    m = GETELEM_HIDE_RE.match(v)
    if m:
        elem_id = m.group("id")
        return ("migrated", f'data-action="hide-element" data-target="#{elem_id}"')

    m = JQUERY_TOGGLE_RE.match(v)
    if m:
        sel = m.group("sel").replace('"', '&quot;')
        return ("migrated", f'data-action="toggle-target" data-target="{sel}"')

    # Simple function call
    m = SIMPLE_CALL_RE.match(v)
    if m:
        fn = m.group(1)
        args_str = m.group(2)
        parsed = parse_args(args_str)
        if parsed is None:
            return ("skip_complex", None)
        # Build data-action and data-arg-N
        attrs = [f'data-{event}-action="{fn}"' if event != "click" else f'data-action="{fn}"']
        for i, arg in enumerate(parsed):
            # Escape quotes in arg
            safe = arg.replace('&', '&amp;').replace('"', '&quot;')
            attrs.append(f'data-arg-{i}="{safe}"')
        return ("migrated", " ".join(attrs))

    return ("skip_complex", None)


def process_file(path: Path, apply: bool) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    stats = {
        "file": rel, "total": 0, "migrated": 0, "skipped": 0,
        "skipped_samples": [],
    }
    new_text_parts: list[str] = []
    last = 0

    for m in HANDLER_RE.finditer(text):
        stats["total"] += 1
        event = m.group(2).lower()
        value = m.group(3)
        status, repl = classify_and_convert(event, value)
        if status == "migrated" and repl is not None:
            new_text_parts.append(text[last:m.start()])
            # m.group(1) is the leading whitespace; preserve it
            new_text_parts.append(m.group(1) + repl)
            last = m.end()
            stats["migrated"] += 1
        else:
            stats["skipped"] += 1
            if len(stats["skipped_samples"]) < 5:
                stats["skipped_samples"].append(f'on{event}="{value[:80]}"')

    new_text_parts.append(text[last:])
    new_text = "".join(new_text_parts)
    if apply and new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--filter", type=str)
    args = ap.parse_args()

    files = sorted(TEMPLATE_ROOT.rglob("*.html"))
    if args.filter:
        files = [f for f in files if args.filter in str(f)]

    all_stats = []
    skipped_counter: Counter[str] = Counter()
    fn_counter: Counter[str] = Counter()
    for f in files:
        s = process_file(f, apply=args.apply)
        all_stats.append(s)
        for sample in s["skipped_samples"]:
            skipped_counter[sample] += 1

    total = sum(s["total"] for s in all_stats)
    migrated = sum(s["migrated"] for s in all_stats)
    skipped = sum(s["skipped"] for s in all_stats)

    print("=" * 70)
    print(f"Mode: {'APPLY' if args.apply else 'REPORT (dry-run)'}")
    print(f"Files scanned: {len(files)}")
    print(f"Total inline handlers: {total}")
    print(f"Migrated: {migrated}")
    print(f"Skipped (manual review): {skipped}")
    print()
    print("Skipped samples (top 30):")
    for sample, cnt in skipped_counter.most_common(30):
        print(f"  {cnt:3d}  {sample}")


if __name__ == "__main__":
    main()
