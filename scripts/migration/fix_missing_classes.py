"""Restore Tailwind utility classes that were dropped by the inline-style
migration. Compares each template against its HEAD revision: for every
`style="..."` in HEAD, ensure the corresponding tag in current has the
matching utility class.

Why this exists:
  The first migration was run against templates with `tw-` prefix, then a
  rollback stripped tw-* classes and partially restored styles. Some style
  restorations were missed (line-number drift in rollback), so when the
  second migration ran (without prefix), it had nothing to migrate for those
  lines. Result: some style="" attributes are gone but their utility class
  was never added. This script reconciles by re-deriving the class from HEAD
  and inserting it where missing.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "app" / "templates"

sys.path.insert(0, str(Path(__file__).parent))
from mapping import map_declaration  # noqa: E402

STYLE_ATTR_RE = re.compile(r'''(\s)style\s*=\s*"([^"]*)"''')
DECLARATION_RE = re.compile(r"\s*([a-zA-Z\-]+)\s*:\s*([^;]+?)\s*(?:;|$)")
JINJA_RE = re.compile(r"\{\{[^}]+\}\}|\{%[^%]+%\}")
CLASS_ATTR_RE = re.compile(r'''class\s*=\s*"([^"]*)"''')


def git_show_head(rel: str) -> str:
    try:
        r = subprocess.run(
            ["git", "show", f"HEAD:{rel}"], cwd=REPO_ROOT,
            capture_output=True, text=True, encoding="utf-8", check=True,
        )
        return r.stdout
    except subprocess.CalledProcessError:
        return ""


def parse_decls(body: str) -> list[tuple[str, str, bool]]:
    out = []
    for m in DECLARATION_RE.finditer(body):
        prop = m.group(1).lower()
        val = " ".join(m.group(2).split())
        is_dyn = bool(JINJA_RE.search(val))
        out.append((prop, val, is_dyn))
    return out


def find_open_tag(text: str, pos: int) -> tuple[int, int] | None:
    s = text.rfind("<", 0, pos)
    if s == -1:
        return None
    i = pos
    q = None
    while i < len(text):
        c = text[i]
        if q:
            if c == q:
                q = None
        else:
            if c in '"\'':
                q = c
            elif c == ">":
                return (s, i + 1)
        i += 1
    return None


def tag_signature(tag: str) -> str:
    """A minimal fingerprint to identify the same tag across versions:
    tag name + every non-style attribute (name + first 30 chars of value)."""
    m = re.match(r"<([a-zA-Z][a-zA-Z0-9\-]*)", tag)
    if not m:
        return ""
    name = m.group(1)
    parts = [name]
    # Strip the tag name then collect attr name="value" tokens
    rest = tag[m.end():].rstrip(">").rstrip("/").strip()
    for attr_m in re.finditer(r'([a-zA-Z][a-zA-Z0-9\-_:]*)\s*=\s*"([^"]*)"', rest):
        n = attr_m.group(1).lower()
        if n == "style":
            continue
        v = attr_m.group(2)[:30]
        parts.append(f"{n}={v}")
    return "|".join(parts)


def find_tag_by_signature(text: str, sig: str, near_line: int) -> tuple[int, int] | None:
    """Find a tag in text that matches the given signature, preferring those
    near the specified line."""
    lines = text.splitlines(keepends=True)
    line_offsets = [0]
    for ln in lines:
        line_offsets.append(line_offsets[-1] + len(ln))
    near_offset = line_offsets[min(near_line, len(line_offsets) - 1)]

    candidates: list[tuple[int, int, int]] = []  # (distance, start, end)
    for tag_m in re.finditer(r"<[a-zA-Z][^>]*>", text):
        tag = tag_m.group(0)
        if tag_signature(tag) == sig:
            distance = abs(tag_m.start() - near_offset)
            candidates.append((distance, tag_m.start(), tag_m.end()))

    if not candidates:
        return None
    candidates.sort()
    _, start, end = candidates[0]
    return (start, end)


def add_classes_to_tag(tag: str, new_classes: list[str]) -> str:
    cm = CLASS_ATTR_RE.search(tag)
    if cm:
        existing = cm.group(1).split()
        merged = existing[:]
        for c in new_classes:
            if c not in existing:
                merged.append(c)
        new_class_attr = f'class="{" ".join(merged)}"'
        return tag[:cm.start()] + new_class_attr + tag[cm.end():]
    # Insert after tag name
    m = re.match(r"<([a-zA-Z][a-zA-Z0-9\-]*)", tag)
    if not m:
        return tag
    return tag[:m.end()] + f' class="{" ".join(new_classes)}"' + tag[m.end():]


def fix_file(path: Path, apply: bool) -> dict:
    rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    head = git_show_head(rel)
    if not head:
        return {"file": rel, "fixes": 0, "skipped": "no head"}
    current = path.read_text(encoding="utf-8", errors="replace")

    fixes = 0
    new_text = current

    # Find every style attribute in HEAD
    head_lines = head.splitlines(keepends=True)
    line_offset = 0
    for ln_no, line in enumerate(head_lines, 1):
        for m in STYLE_ATTR_RE.finditer(line):
            style_body = m.group(2)
            decls = parse_decls(style_body)
            if not decls or any(d[2] for d in decls):
                continue
            # Map to classes
            classes: list[str] = []
            unmappable = False
            for prop, val, _ in decls:
                cls = map_declaration(prop, val)
                if cls is None:
                    unmappable = True
                    break
                classes.extend(cls.split())
            if unmappable or not classes:
                continue

            # Find the HEAD tag containing this style
            head_pos = sum(len(l) for l in head_lines[:ln_no - 1]) + m.start()
            head_tag_bounds = find_open_tag(head, head_pos)
            if not head_tag_bounds:
                continue
            head_tag = head[head_tag_bounds[0]:head_tag_bounds[1]]
            sig = tag_signature(head_tag)
            if not sig:
                continue

            # Find the matching tag in current
            cur_bounds = find_tag_by_signature(new_text, sig, ln_no)
            if not cur_bounds:
                continue
            cur_tag = new_text[cur_bounds[0]:cur_bounds[1]]
            # Check if all required classes already present
            cm = CLASS_ATTR_RE.search(cur_tag)
            existing = cm.group(1).split() if cm else []
            missing = [c for c in classes if c not in existing]
            if not missing:
                continue
            new_tag = add_classes_to_tag(cur_tag, missing)
            new_text = new_text[:cur_bounds[0]] + new_tag + new_text[cur_bounds[1]:]
            fixes += 1

    if apply and new_text != current:
        path.write_text(new_text, encoding="utf-8")
    return {"file": rel, "fixes": fixes}


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = sorted(TEMPLATE_ROOT.rglob("*.html"))
    total_fixes = 0
    fixed_files = 0
    for f in files:
        s = fix_file(f, apply=args.apply)
        if s.get("fixes", 0) > 0:
            print(f"  {s['fixes']:4d}  {s['file']}")
            total_fixes += s["fixes"]
            fixed_files += 1
    mode = "APPLIED" if args.apply else "DRY RUN"
    print(f"\n{mode}: {total_fixes} class restorations across {fixed_files} files")


if __name__ == "__main__":
    main()
