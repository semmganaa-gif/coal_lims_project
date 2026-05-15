"""External `<script src="...">` тагуудад `defer` attribute системээр нэмэх.

Sprint 1.1d (CSP) + Sprint 2 (Vite bundle)-ийн араас:
  - Vite-ийн `<script type="module">` нь deferred-аар ажилладаг — parsing
    дууссаны дараа execute хийгдэнэ. Тиймээс `window.$`, `window.bootstrap`,
    `window.Alpine` зэрэг global-ыг module bundle тогтоох ёстой ч parsing
    үед хүрэлцэхгүй.
  - Энгийн `<script src="...">` нь parsing үед шууд execute хийгдэнэ —
    module bundle-аас өмнө ажилладаг тул global-уудыг ашигладаг скрипт
    бүгд алдана.
  - `defer` attribute нэмэх нь scripts-ийг module bundle-тай адил queue-д
    оруулж document order-оор execute хийгдэхийг баталгаажуулна. Bundle нь
    base.html дотор эхэнд орсон тул global-ууд бэлэн болсон үед бусад скрипт
    ажиллана.

Зөвхөн `src="..."` бүхий external скрипт-ийг өөрчилнө; inline `<script>`
блок-уудыг гар тус бүрд `DOMContentLoaded`-аар цэгцэлнэ.

Алгасах нөхцөл:
  - `defer` эсвэл `async` аль хэдийн байгаа
  - `type="module"` (auto-deferred)
  - Vite-ийн `vite_js_tag(...)` Jinja helper (өөрөө module гаргадаг)
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

# Windows console-д Кирилл бичих
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "app" / "templates"

# `<script src="..."></script>` загвар (нэг мөрөнд) — defer/async/module байхгүй
SCRIPT_RE = re.compile(
    r'<script\s+src="([^"]+)"([^>]*)>\s*</script>',
    flags=re.IGNORECASE,
)


# Head-д sync ачаалагдаж inline body scripts-д шууд хэрэглэгддэг файлууд:
# энэ файлуудыг defer хийвэл inline `logger.log(...)` гэх мэт parse-time
# дуудлага алдах. Тиймээс exclusion list-д орно.
SYNC_REQUIRED = {
    "js/utils/logger.js",  # window.logger — aggrid_macros болон бусад inline-аас
}


def needs_defer(src: str, attrs: str) -> bool:
    """`defer` нэмэхийг шаардах эсэх — attribute + filename-аас үндэслэн."""
    lowered = attrs.lower()
    if "defer" in lowered:
        return False
    if "async" in lowered:
        return False
    if 'type="module"' in lowered or "type='module'" in lowered:
        return False
    # Sync ачаалал шаардлагатай файлуудыг алгасах
    for sync_path in SYNC_REQUIRED:
        if sync_path in src:
            return False
    return True


def transform(content: str) -> tuple[str, int]:
    """Файлын агуулгад defer нэмэх."""
    count = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal count
        src = match.group(1)
        attrs = match.group(2) or ""
        if not needs_defer(src, attrs):
            return match.group(0)
        count += 1
        # attrs нь "" эсвэл " type='text/javascript'" гэх мэт байж болно
        # attrs-ийн өмнө сүүлийн whitespace байгаа эсэхийг хадгалах
        attrs_stripped = attrs.rstrip()
        return f'<script src="{src}"{attrs_stripped} defer></script>'

    new_content = SCRIPT_RE.sub(_replace, content)
    return new_content, count


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
    print(f"\n{mode} {total_files} файл, {total_changes} <script> tag-д defer нэмсэн")
    return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    sys.exit(main(dry_run=dry))
