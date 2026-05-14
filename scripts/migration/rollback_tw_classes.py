"""Rollback the `tw-*` Tailwind class additions made by migrate_inline_styles.py
and restore the original `style="..."` attributes from git HEAD.

This re-runs the migration cleanly with an updated mapping table.

Strategy:
  1. For each template, read git HEAD version (pre-migration baseline).
  2. Diff with current. The current state = HEAD + CSP-era changes + migration.
     We want to keep CSP-era changes but undo migration.
  3. Walk the current file, find every <tag class="..."> that contains tw-* classes:
     - Remove all tw-* classes from the class attribute
     - If the matching tag in HEAD has style="...", restore it
  4. If git HEAD differs from current beyond migration, this is best-effort.

Simpler alternative (used here):
  Remove tw-* class fragments and look up the original style="..." from HEAD
  for that exact tag (matching by line number + tag name + outer class). This
  works because migration was the most recent edit to those tags.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "app" / "templates"


def git_show_head(rel_path: str) -> str:
    """Read a file as it exists in git HEAD."""
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{rel_path}"],
            cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8",
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


# Match a class attribute that contains at least one tw-* class
CLASS_WITH_TW_RE = re.compile(r'''class\s*=\s*"([^"]*\btw-[^"]*)"''')

# Match individual tw-* class tokens (handles arbitrary values: tw-w-[100px])
TW_TOKEN_RE = re.compile(r'\btw-[a-zA-Z0-9_/.\-]+(?:\[[^\]]+\])?[!]?')


def strip_tw_classes(file_text: str) -> str:
    """Remove all `tw-*` class tokens from class="..." attributes.
    If the resulting class attribute is empty, remove it entirely.
    """
    def _repl(m: re.Match) -> str:
        body = m.group(1)
        # Remove tw-* tokens; collapse whitespace
        cleaned = TW_TOKEN_RE.sub("", body)
        cleaned = " ".join(cleaned.split())
        if not cleaned:
            return ""  # remove the class attribute entirely
        return f'class="{cleaned}"'

    # First, replace class="..." that has tw- inside
    new_text = CLASS_WITH_TW_RE.sub(_repl, file_text)
    # Clean up double spaces and dangling whitespace before/after attribute removal
    new_text = re.sub(r'  +', ' ', new_text)
    new_text = re.sub(r' +>', '>', new_text)
    return new_text


def main() -> None:
    files = sorted(TEMPLATE_ROOT.rglob("*.html"))
    changed = 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        if "tw-" not in text:
            continue
        new = strip_tw_classes(text)
        if new != text:
            f.write_text(new, encoding="utf-8")
            changed += 1
    print(f"Stripped tw-* classes from {changed} files")

    # Now restore style="..." attrs from HEAD using a per-tag merge.
    # Strategy: scan HEAD version and current version side-by-side, matching
    # tag positions. For tags that exist in HEAD with style="...", inject the
    # style back into the current version.
    restored = 0
    for f in files:
        rel = str(f.relative_to(REPO_ROOT)).replace("\\", "/")
        head_text = git_show_head(rel)
        if not head_text:
            continue
        current_text = f.read_text(encoding="utf-8", errors="replace")
        if 'style="' not in head_text:
            continue
        merged = merge_styles_from_head(head_text, current_text)
        if merged != current_text:
            f.write_text(merged, encoding="utf-8")
            restored += 1
    print(f"Restored style=\"\" attrs from HEAD in {restored} files")


# ---------------------------------------------------------------------------
# HEAD style= restoration
# ---------------------------------------------------------------------------
# Naive approach: for each <tag ... style="..."> in HEAD, find the SAME tag
# (matching by tag name, structure, inner-attr) in current text and inject
# the style back. This works if tag positions are stable.

STYLE_ATTR_RE = re.compile(r'''(\s)style\s*=\s*"([^"]*)"''')


def merge_styles_from_head(head: str, current: str) -> str:
    """Re-inject style="..." from HEAD into current, matching by line.
    Same-line tag is detected by tag name + first attribute fingerprint.
    """
    head_lines = head.splitlines(keepends=True)
    cur_lines = current.splitlines(keepends=True)

    # Quick guard: if line counts differ heavily, skip restoration to avoid
    # corruption.
    if abs(len(head_lines) - len(cur_lines)) > 20:
        return current

    out: list[str] = []
    n = max(len(head_lines), len(cur_lines))
    for i in range(n):
        cur_line = cur_lines[i] if i < len(cur_lines) else ""
        head_line = head_lines[i] if i < len(head_lines) else ""
        # Find style= in head_line
        head_styles = list(STYLE_ATTR_RE.finditer(head_line))
        if not head_styles:
            out.append(cur_line)
            continue
        # Inject each style= into cur_line at the same opening tag.
        # Approach: match by character position — replace cur_line = head_line
        # if both lines look structurally similar (same tag at same position).
        # Conservative fallback: only restore if cur_line has the same
        # `<tag ...>` opening as head_line up to the style= attribute.
        new_cur = cur_line
        for m in head_styles:
            style_text = m.group(0).strip()  # e.g. style="display:none"
            # Find the open tag containing m in head_line
            tag_start = head_line.rfind("<", 0, m.start())
            if tag_start < 0:
                continue
            tag_open = head_line[tag_start: m.start()].strip()
            # Look for the same tag_open in cur_line
            cur_pos = new_cur.find(tag_open)
            if cur_pos == -1:
                continue
            # Find the end of this tag (>) in cur_line
            close_idx = new_cur.find(">", cur_pos)
            if close_idx == -1:
                continue
            # Insert style= just before the > if not already present
            tag_region = new_cur[cur_pos:close_idx]
            if 'style="' in tag_region:
                continue
            new_cur = (
                new_cur[:close_idx]
                + " " + style_text
                + new_cur[close_idx:]
            )
        out.append(new_cur)
    return "".join(out)


if __name__ == "__main__":
    main()
