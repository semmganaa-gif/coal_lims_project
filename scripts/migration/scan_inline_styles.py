"""Scan all template files for inline style attributes and produce a frequency report.

Usage:
    python scripts/migration/scan_inline_styles.py

Output:
    scripts/migration/inline_styles_report.json — full per-occurrence list
    scripts/migration/inline_styles_summary.txt — frequency-sorted unique declarations

Purpose: input for the mapping table that drives the migration script.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "app" / "templates"

STYLE_ATTR_RE = re.compile(r'''style\s*=\s*"([^"]*)"''')
DECLARATION_RE = re.compile(r"\s*([a-zA-Z\-]+)\s*:\s*([^;]+?)\s*(?:;|$)")
JINJA_INTERPOLATION_RE = re.compile(r"\{\{[^}]+\}\}|\{%[^%]+%\}")


def normalize_value(value: str) -> str:
    """Collapse whitespace inside a CSS declaration value."""
    return " ".join(value.split())


def parse_declarations(style_value: str) -> list[tuple[str, str, bool]]:
    """Return list of (property, value, is_dynamic) tuples for a style attribute body."""
    declarations: list[tuple[str, str, bool]] = []
    for match in DECLARATION_RE.finditer(style_value):
        prop = match.group(1).lower()
        raw_value = match.group(2)
        is_dynamic = bool(JINJA_INTERPOLATION_RE.search(raw_value))
        declarations.append((prop, normalize_value(raw_value), is_dynamic))
    return declarations


def scan_template(path: Path) -> list[dict]:
    """Yield every inline style attribute occurrence in the file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    occurrences = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for m in STYLE_ATTR_RE.finditer(line):
            raw_value = m.group(1)
            declarations = parse_declarations(raw_value)
            occurrences.append({
                "file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "line": line_no,
                "raw": raw_value,
                "declarations": [
                    {"prop": p, "value": v, "dynamic": d}
                    for p, v, d in declarations
                ],
            })
    return occurrences


def main() -> int:
    all_occurrences: list[dict] = []
    for tpl in TEMPLATE_ROOT.rglob("*.html"):
        all_occurrences.extend(scan_template(tpl))

    # Per-declaration frequency
    declaration_counter: Counter[tuple[str, str]] = Counter()
    dynamic_declarations: list[tuple[str, str, str, int]] = []
    files_per_decl: defaultdict[tuple[str, str], set[str]] = defaultdict(set)

    for occ in all_occurrences:
        for d in occ["declarations"]:
            key = (d["prop"], d["value"])
            if d["dynamic"]:
                dynamic_declarations.append((d["prop"], d["value"], occ["file"], occ["line"]))
            else:
                declaration_counter[key] += 1
                files_per_decl[key].add(occ["file"])

    # Whole-attribute frequency (e.g. "display:none; flex:1")
    raw_attr_counter: Counter[str] = Counter(
        normalize_value(o["raw"]) for o in all_occurrences
        if not any(d["dynamic"] for d in o["declarations"])
    )

    out_dir = Path(__file__).parent
    report_path = out_dir / "inline_styles_report.json"
    summary_path = out_dir / "inline_styles_summary.txt"

    report_path.write_text(
        json.dumps({
            "total_occurrences": len(all_occurrences),
            "total_unique_declarations": len(declaration_counter),
            "dynamic_count": len(dynamic_declarations),
            "occurrences": all_occurrences,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines: list[str] = []
    lines.append(f"Total inline style attributes: {len(all_occurrences)}")
    lines.append(f"Unique CSS declarations:       {len(declaration_counter)}")
    lines.append(f"Dynamic (Jinja-templated):     {len(dynamic_declarations)}")
    lines.append("")
    lines.append("=" * 70)
    lines.append("Top 80 declarations by frequency")
    lines.append("=" * 70)
    for (prop, value), count in declaration_counter.most_common(80):
        files = files_per_decl[(prop, value)]
        lines.append(f"{count:5d}  {prop}: {value}    ({len(files)} files)")

    lines.append("")
    lines.append("=" * 70)
    lines.append(f"Dynamic declarations ({len(dynamic_declarations)})")
    lines.append("=" * 70)
    for prop, value, file, line_no in dynamic_declarations:
        lines.append(f"  {file}:{line_no}  {prop}: {value}")

    lines.append("")
    lines.append("=" * 70)
    lines.append("Top 30 raw style attributes (full strings)")
    lines.append("=" * 70)
    for raw, count in raw_attr_counter.most_common(30):
        lines.append(f"{count:5d}  style=\"{raw}\"")

    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {report_path}")
    print(f"Wrote {summary_path}")
    print(f"\nTotal: {len(all_occurrences)} inline styles, "
          f"{len(declaration_counter)} unique declarations, "
          f"{len(dynamic_declarations)} dynamic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
