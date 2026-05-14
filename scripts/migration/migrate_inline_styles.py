"""Migrate `style="..."` attributes to `class="tw-..."` Tailwind utilities.

Modes:
    --report   Scan only; output per-file mapping plan + unmappable list.
    --apply    Modify templates in place.

Strategy:
    For each `style="..."` occurrence, try to map every CSS declaration via
    mapping.py. If ALL declarations map → replace entire style attribute with
    Tailwind class(es), merging into existing class attribute if present.
    If ANY declaration is unmappable → leave the file unchanged at that
    location and record it for manual review.

    Dynamic (Jinja-templated) style attributes are ALWAYS skipped — handled
    in a separate pass.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "app" / "templates"

sys.path.insert(0, str(Path(__file__).parent))
from mapping import map_declaration  # noqa: E402

JINJA_INTERPOLATION_RE = re.compile(r"\{\{[^}]+\}\}|\{%[^%]+%\}|\$\{[^}]+\}|'\s*\+\s*\w")
DECLARATION_SPLIT_RE = re.compile(r"\s*([a-zA-Z\-]+)\s*:\s*([^;]+?)\s*(?:;|$)")

# Match the entire opening tag attributes region we need to manipulate.
# Strategy: locate <tag ...style="..."...> then within the same tag find class="...".
# To keep regex simple, parse each line/tag region.

# Match: style="..." capturing the body and its full match span
STYLE_ATTR_RE = re.compile(r'''(\s)style\s*=\s*"([^"]*)"''')


def parse_declarations(body: str) -> list[tuple[str, str, bool]]:
    decls: list[tuple[str, str, bool]] = []
    for m in DECLARATION_SPLIT_RE.finditer(body):
        prop = m.group(1).lower()
        raw_value = " ".join(m.group(2).split())
        is_dynamic = bool(JINJA_INTERPOLATION_RE.search(raw_value))
        decls.append((prop, raw_value, is_dynamic))
    return decls


def find_open_tag_bounds(text: str, style_pos: int) -> tuple[int, int] | None:
    """Find the bounds of the opening tag containing style_pos.

    Returns (start, end) where text[start] == '<' and text[end-1] == '>'.
    """
    # Walk backwards to find '<'
    start = text.rfind("<", 0, style_pos)
    if start == -1:
        return None
    # Walk forwards from style_pos to find next '>' that is not inside quotes.
    i = style_pos
    in_quote: str | None = None
    while i < len(text):
        ch = text[i]
        if in_quote:
            if ch == in_quote:
                in_quote = None
        else:
            if ch in '"\'':
                in_quote = ch
            elif ch == ">":
                return (start, i + 1)
        i += 1
    return None


CLASS_ATTR_RE = re.compile(r'''class\s*=\s*"([^"]*)"''')


def merge_classes_into_tag(tag: str, new_classes: list[str], style_match_span: tuple[int, int]) -> str:
    """Inside `tag` (the full <...> region), remove the style attr at the given
    span and merge new_classes into the class attribute (creating it if absent).
    """
    s_start, s_end = style_match_span
    # Remove the style attribute (and the leading whitespace captured by group 1)
    tag_without_style = tag[:s_start] + tag[s_end:]

    # Now insert/merge classes
    cm = CLASS_ATTR_RE.search(tag_without_style)
    new_class_str = " ".join(new_classes)
    if cm:
        existing = cm.group(1)
        # Avoid duplicate class entries (preserve order)
        existing_set = existing.split()
        merged = existing_set[:]
        for c in new_classes:
            if c not in existing_set:
                merged.append(c)
        new_class_attr = f'class="{" ".join(merged)}"'
        result = tag_without_style[:cm.start()] + new_class_attr + tag_without_style[cm.end():]
    else:
        # Insert class="..." right after the tag name
        # Find the first whitespace after `<tagname`
        m = re.match(r"<([a-zA-Z][a-zA-Z0-9\-]*)", tag_without_style)
        if not m:
            return tag  # bail, shouldn't happen
        insert_pos = m.end()
        result = (
            tag_without_style[:insert_pos]
            + f' class="{new_class_str}"'
            + tag_without_style[insert_pos:]
        )
    return result


def process_file(path: Path, apply: bool) -> dict:
    """Returns stats for this file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    original = text

    stats = {
        "file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "total": 0,
        "migrated": 0,
        "skipped_dynamic": 0,
        "skipped_unmappable": 0,
        "unmappable_decls": [],  # list of (prop, value)
    }

    # We process tag-by-tag from the END of file backwards to keep offsets valid
    # while we make edits.
    matches = list(STYLE_ATTR_RE.finditer(text))
    matches.reverse()

    new_text = text
    for m in matches:
        stats["total"] += 1
        style_body = m.group(2)
        decls = parse_declarations(style_body)
        if not decls:
            continue
        if any(d[2] for d in decls):
            stats["skipped_dynamic"] += 1
            continue

        # Map each declaration
        mapped: list[str] = []
        unmappable: list[tuple[str, str]] = []
        for prop, value, _ in decls:
            cls = map_declaration(prop, value)
            if cls is None:
                unmappable.append((prop, value))
            else:
                # mapped class can contain multiple space-separated classes (border shorthand)
                mapped.extend(cls.split())

        if unmappable:
            stats["skipped_unmappable"] += 1
            stats["unmappable_decls"].extend(unmappable)
            continue

        # Find tag bounds, replace style attr, merge classes
        tag_bounds = find_open_tag_bounds(new_text, m.start())
        if not tag_bounds:
            stats["skipped_unmappable"] += 1
            continue
        t_start, t_end = tag_bounds
        tag = new_text[t_start:t_end]
        # Locate the style match within tag-local coords
        style_local_start = m.start() - t_start
        style_local_end = m.end() - t_start
        new_tag = merge_classes_into_tag(tag, mapped, (style_local_start, style_local_end))
        new_text = new_text[:t_start] + new_tag + new_text[t_end:]
        stats["migrated"] += 1

    if apply and new_text != original:
        path.write_text(new_text, encoding="utf-8")

    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Modify files in place")
    ap.add_argument("--limit", type=int, help="Process only first N templates (debug)")
    ap.add_argument("--filter", type=str, help="Substring filter on file path")
    args = ap.parse_args()

    files = sorted(TEMPLATE_ROOT.rglob("*.html"))
    if args.filter:
        files = [f for f in files if args.filter in str(f)]
    if args.limit:
        files = files[: args.limit]

    all_stats = []
    unmappable_counter: Counter[tuple[str, str]] = Counter()
    for f in files:
        s = process_file(f, apply=args.apply)
        all_stats.append(s)
        for d in s["unmappable_decls"]:
            unmappable_counter[d] += 1

    total = sum(s["total"] for s in all_stats)
    migrated = sum(s["migrated"] for s in all_stats)
    skipped_dyn = sum(s["skipped_dynamic"] for s in all_stats)
    skipped_unm = sum(s["skipped_unmappable"] for s in all_stats)

    print("=" * 70)
    print(f"Mode: {'APPLY (in-place)' if args.apply else 'REPORT (dry-run)'}")
    print(f"Files scanned:        {len(files)}")
    print(f"Total style attrs:    {total}")
    print(f"Migrated:             {migrated}")
    print(f"Skipped (dynamic):    {skipped_dyn}")
    print(f"Skipped (unmappable): {skipped_unm}")
    print()
    print(f"Unmappable declarations (top 40):")
    for (prop, value), cnt in unmappable_counter.most_common(40):
        print(f"  {cnt:5d}  {prop}: {value}")

    # Dump JSON report alongside
    out_path = Path(__file__).parent / "migrate_report.json"
    out_path.write_text(
        json.dumps(
            {
                "mode": "apply" if args.apply else "report",
                "totals": {
                    "files": len(files),
                    "style_attrs": total,
                    "migrated": migrated,
                    "skipped_dynamic": skipped_dyn,
                    "skipped_unmappable": skipped_unm,
                },
                "unmappable": [
                    {"prop": p, "value": v, "count": c}
                    for (p, v), c in unmappable_counter.most_common()
                ],
                "per_file": all_stats,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nReport written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
