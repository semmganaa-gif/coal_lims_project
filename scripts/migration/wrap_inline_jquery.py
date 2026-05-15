"""Inline `<script>` блок дотрох `$(document).ready(...)` / `$(function...)`-г
`document.addEventListener('DOMContentLoaded', ...)`-аар орлуулах.

Шалтгаан:
  Vite ES module bundle (main.js) нь defer-аар ажилладаг — parse дууссаны
  дараа execute хийгдэж `window.$ = jQuery` тогтооно. Inline `<script>` блок
  parse-ийн үед шууд ажилладаг тул `$` undefined байгаа → `$(document).ready`
  нь "TypeError: $ is not a function" алдааг шидэнэ.

  `document.addEventListener('DOMContentLoaded', fn)` нь runtime API
  бөгөөд `$`-аас үл хамаарна. DOMContentLoaded event нь deferred scripts
  бүгд гүйцэтгэгдсэний дараа дуугардаг тул callback дотор `$` бэлэн байна.

Хувиргалт:
  $(document).ready(function(...){...});  →  document.addEventListener('DOMContentLoaded', function(...){...});
  $(function(...){...});                    →  document.addEventListener('DOMContentLoaded', function(...){...});

Олон мөртэй блокын дотор `$('...')` гэх мэт дуудлага DOMContentLoaded
callback-ийн дотор байх тул засвар хэрэггүй.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "app" / "templates"

# `$(document).ready(function(args) {`  →  `document.addEventListener('DOMContentLoaded', function(args) {`
READY_RE = re.compile(
    r'\$\(\s*document\s*\)\.ready\(\s*function\s*\(([^)]*)\)\s*\{',
    flags=re.MULTILINE,
)

# `$(function(args) {`  →  `document.addEventListener('DOMContentLoaded', function(args) {`
SHORT_RE = re.compile(
    r'\$\(\s*function\s*\(([^)]*)\)\s*\{',
    flags=re.MULTILINE,
)


def transform(content: str) -> tuple[str, int]:
    count = 0

    def _replace_ready(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        args = match.group(1)
        return f"document.addEventListener('DOMContentLoaded', function({args}) {{"

    def _replace_short(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        args = match.group(1)
        return f"document.addEventListener('DOMContentLoaded', function({args}) {{"

    content = READY_RE.sub(_replace_ready, content)
    content = SHORT_RE.sub(_replace_short, content)
    return content, count


def main(dry_run: bool = False) -> int:
    total_files = 0
    total_changes = 0

    for html_file in sorted(TEMPLATE_ROOT.rglob("*.html")):
        content = html_file.read_text(encoding="utf-8")
        new_content, count = transform(content)
        if count > 0:
            total_files += 1
            total_changes += count
            rel = html_file.relative_to(REPO_ROOT)
            print(f"  {rel}: +{count}")
            if not dry_run:
                html_file.write_text(new_content, encoding="utf-8")

    mode = "[DRY-RUN]" if dry_run else "[APPLIED]"
    print(f"\n{mode} {total_files} файл, {total_changes} jQuery ready-блок засагдсан")
    return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    sys.exit(main(dry_run=dry))
