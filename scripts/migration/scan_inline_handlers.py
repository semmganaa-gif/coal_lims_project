"""Scan all template files for inline event handlers (`onclick="..."`, etc.)
and produce a frequency / pattern report to drive Sprint 1.1b migration.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "app" / "templates"

# Match `onevent="..."` inside an HTML opening tag.
HANDLER_RE = re.compile(r'''\bon([a-z]+)\s*=\s*"([^"]*)"''')

# Common patterns we want to recognize and migrate uniformly.
PATTERN_RE = {
    "history_back": re.compile(r"^\s*history\.back\(\s*\)\s*;?\s*$"),
    "location_reload": re.compile(r"^\s*location\.reload\(\s*\)\s*;?\s*$"),
    "window_print": re.compile(r"^\s*window\.print\(\s*\)\s*;?\s*$"),
    "form_submit": re.compile(r"^\s*(this\.form|this)\.submit\(\s*\)\s*;?\s*$"),
    "return_confirm": re.compile(r"^\s*return\s+confirm\((['\"])(?P<msg>.+?)\1\)\s*;?\s*$"),
    "function_call_simple": re.compile(r"^\s*([A-Za-z_][\w]*)\s*\(\s*([^)]*)\s*\)\s*;?\s*$"),
    "method_call_event": re.compile(r"^\s*([A-Za-z_][\w]*\.[A-Za-z_][\w]*)\s*\(\s*event\s*\)\s*;?\s*$"),
    "set_value_simple": re.compile(r"^\s*this\.value\s*=\s*[^;]+;?\s*$"),
    "open_window": re.compile(r"^\s*window\.open\("),
}


def classify(value: str) -> str:
    v = value.strip()
    for name, pattern in PATTERN_RE.items():
        if pattern.match(v):
            return name
    if "this.form.submit" in v:
        return "form_submit"
    if v.startswith("return "):
        return "return_complex"
    if "javascript:" in v.lower():
        return "javascript_protocol"
    return "complex_inline"


def main() -> None:
    counter_per_event: Counter[str] = Counter()
    counter_per_pattern: Counter[tuple[str, str]] = Counter()
    counter_per_function: Counter[str] = Counter()
    samples_per_pattern: defaultdict[str, list[str]] = defaultdict(list)
    files_per_function: defaultdict[str, set[str]] = defaultdict(set)
    full_occurrences: list[dict] = []

    for tpl in sorted(TEMPLATE_ROOT.rglob("*.html")):
        text = tpl.read_text(encoding="utf-8", errors="replace")
        rel = str(tpl.relative_to(REPO_ROOT)).replace("\\", "/")
        for line_no, line in enumerate(text.splitlines(), 1):
            for m in HANDLER_RE.finditer(line):
                event = m.group(1).lower()
                value = m.group(2)
                category = classify(value)
                counter_per_event[event] += 1
                counter_per_pattern[(event, category)] += 1
                # Track function name if simple call
                fn_match = re.match(r"^\s*([A-Za-z_][\w]*)\s*\(", value)
                if fn_match:
                    fn = fn_match.group(1)
                    counter_per_function[fn] += 1
                    files_per_function[fn].add(rel)
                if len(samples_per_pattern[category]) < 4:
                    samples_per_pattern[category].append(f"{rel}:{line_no}  on{event}=\"{value[:80]}\"")
                full_occurrences.append({
                    "file": rel, "line": line_no,
                    "event": event, "value": value,
                    "category": category,
                })

    out_dir = Path(__file__).parent
    (out_dir / "inline_handlers_report.json").write_text(
        json.dumps({
            "total": len(full_occurrences),
            "occurrences": full_occurrences,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines: list[str] = []
    lines.append(f"Total inline event handlers: {len(full_occurrences)}")
    lines.append("")
    lines.append("=" * 70)
    lines.append("By event type")
    lines.append("=" * 70)
    for evt, cnt in counter_per_event.most_common():
        lines.append(f"  {cnt:5d}  on{evt}")

    lines.append("")
    lines.append("=" * 70)
    lines.append("By pattern (event × category)")
    lines.append("=" * 70)
    for (evt, cat), cnt in counter_per_pattern.most_common():
        lines.append(f"  {cnt:5d}  on{evt:<10s} {cat}")

    lines.append("")
    lines.append("=" * 70)
    lines.append("Top called functions (likely to migrate as named handlers)")
    lines.append("=" * 70)
    for fn, cnt in counter_per_function.most_common(30):
        files = files_per_function[fn]
        lines.append(f"  {cnt:5d}  {fn}()    [{len(files)} files]")

    lines.append("")
    lines.append("=" * 70)
    lines.append("Pattern samples (up to 4 per category)")
    lines.append("=" * 70)
    for cat in sorted(samples_per_pattern.keys()):
        lines.append(f"\n--- {cat} ---")
        for s in samples_per_pattern[cat]:
            lines.append(f"  {s}")

    summary = "\n".join(lines)
    (out_dir / "inline_handlers_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
