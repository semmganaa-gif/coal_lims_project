# Session лог — 2026-05-09 (Бямба гариг)

**Хугацаа:** ~12:00–17:00 (~5 цаг)
**Анхдагч зорилго:** CSP "Applying inline style violates" алдааг зөв замаар шийдэх (түр засваргүй)
**Эцсийн төлөв:** Хэсэгчлэн дуусав. Navbar-ийн меню хэрэглэгчид харагдахгүй байгаа гол асуудал шийдэгдээгүй.

---

## 1. Анхдагч асуудал

Хэрэглэгч төслөө өөр компьютероос ачаалаад ажиллуулсны дараа browser console-д CSP алдаа гарсан:

```
Applying inline style violates the following Content Security Policy directive
'style-src 'self' 'nonce-...' 'unsafe-inline' ...'.
Note that 'unsafe-inline' is ignored if either a hash or nonce value is present
in the source list. The action has been blocked.
```

**Шалтгаан:** 04-22-ний session-аар CSP-д nonce нэмсэн ч template-ээс inline style/handler-ийг арилгаагүй. CSP3-ийн дагуу nonce байхад `'unsafe-inline'` автоматаар үл тоомсорлогддог тул бүх inline style блоклогдсон.

---

## 2. Хийсэн ажил (өнөөдөр)

### 2.1 Foundation — Tailwind v4 + Vite

- `package.json`-д Tailwind v4.3.0 + `@tailwindcss/vite` v4.3.0 install
- `src/styles.css` — `@theme` дотор лабын домэйн семантик токен:
  - `--color-pass/warn/fail/info-2/accent` (Bootstrap-тай collision-гүй нэртэй)
  - `--text-3xs/2xs/xs-1/xs-2/xs-3/sm-1/sm-2/sm-3` (төслийн dense table-д тохируулсан)
- `app/utils/vite_assets.py` — Vite manifest-ийг nonce-той CSS link tag болгон үзүүлэх helper
- `app/bootstrap/jinja.py` — `vite_css_tag`/`vite_asset` Jinja global-ууд бүртгэх
- `vite.config.js` — `@tailwindcss/vite` plugin

### 2.2 Migration scripts (`scripts/migration/`)

- `scan_inline_styles.py` — 201 template-аас бүх inline style scan
- `mapping.py` — CSS declaration → Tailwind class хөрвүүлэгч (~330 мөр)
- `migrate_inline_styles.py` — automated bulk migration (dry-run/apply mode)
- `rollback_tw_classes.py` — `tw-` prefix-тэй migration-ыг буцаах script
- `fix_missing_classes.py` — Rollback-ын дараа сэргэж чадаагүй class-уудыг HEAD-аас сэргээх
- `scan_inline_handlers.py` — 140 inline event handler scan
- `migrate_inline_handlers.py` — `onclick=""` → `data-action`

### 2.3 CSP-safe runtime infrastructure

- `app/static/js/csp_handlers.js` — `LIMS_ACTIONS` dispatch table + event delegation:
  - 14 built-in action (reload/back/print/navigate/toggle-target гэх мэт)
  - `data-arg-N` reader (`this.value`, `this.checked` зэрэг coerce-тэй)
  - Fallback: `window[fnName]`-ыг шууд дуудах
- `app/static/js/dynamic_styles.js` — runtime style mutation:
  - `data-bg-color/text-color/border-color/anim-delay-index/progress` гэх мэт
  - MutationObserver — 3rd-party widget (Tabulator/AG Grid) рүү шинээр insert хийсэн HTML-ийн data-* атрибутыг auto apply

### 2.4 Migration үр дүн

| Зүйл | Тоо | Status |
|---|---|---|
| Inline `style=""` | 1,151 → 0 | ✅ Бүгд class руу |
| Inline event handler | 140 → 0 | ✅ Бүгд `data-action` руу |
| Dynamic Jinja style (loop animation, dynamic color) | 10 | ✅ `data-*` + JS dispatch |
| JS template literal `${...}` дотор inline style | 9 | ✅ Шууд DOM API эсвэл `data-*` |
| chat.js runtime `<style>` injection | 1 | ✅ Static CSS-д шилжсэн |
| htmx style injection | 1 | ✅ `includeIndicatorStyles=false` + static CSS |

### 2.5 CSP3 архитектур

```
default-src 'self'
script-src 'self' 'nonce-X' 'unsafe-eval' [CDN]   ← Alpine.js eval
script-src-elem 'self' 'nonce-X' [CDN]            ← <script> блок
script-src-attr 'none'                            ← inline onclick БЛОКЛОВ
style-src-elem 'self' 'nonce-X' [CDN]             ← <style> блок
style-src-attr 'unsafe-inline'                    ← runtime element.style
```

---

## 3. Бүтэлгүйтэл / Алдаатай шийдвэр

### 3.1 Tailwind v4 `prefix(tw)` regression — ~90 минутын dead end

**Хийсэн:** `@import "tailwindcss" prefix(tw);` ашиглан `tw-` prefix-тэй ажиллуулах оролдлого. Bootstrap-тай collision үгүй болох зорилготой.

**Үр дүн:** Tailwind v4.3.0 (болон v4.0.17)-д prefix-тэй үед content scanning ажиллахгүй. Templates-аас class detect хийхгүй, utility generate хийхгүй. CLI-ээс ч ажиллаагүй. Tailwind source code-ийн @import parser-ийг ширтсэн — `prefix()` параметрыг хүлээж авдаггүй болж тогтоосон.

**Шийдвэр:** prefix-гүйгээр явах. Bootstrap-тай collision-аас зайлсхийхийн тулд:
- Семантик token нэр: `pass/warn/fail/info-2` (BS-ийн `success/warning/danger/info`-тай collision-гүй)
- Spacing scale: `m-3/4/5` зэрэг collision-той тохиолдолд автоматаар arbitrary value (`m-[12px]`) emit хийх

### 3.2 Migration script bug-ууд

1. **Jinja function call-ыг HTML attr-тай андуурсан**
   - HEAD-д: `{{ subfield(class="", style="display:none;") }}` — Jinja macro дуудлага
   - Migration: `style="..."` regex таалаад `style="display:none;"`-ыг устгасан → `{{ subfield(class="", ) }}` гажиг → Jinja parse error
   - Засвар: гарт оруулсан, `add_sample.html`-д тохиолдсон ганц газар

2. **Rollback merge_styles_from_head-ийн line drift**
   - tw- prefix-тэй migration-ыг rollback хийхдээ HEAD-аас `style="..."`-уудыг сэргээх ёстой байсан
   - Жижиг indentation өөрчлөлтөөс болж зарим style сэргэгдэхгүй үлдсэн
   - Дараагийн migration (prefix-гүй) тэдгээрийг хараагүй → class нэмэгдээгүй
   - **378 ширхэг class** алдагдсан (68 файлд)
   - Засвар: `fix_missing_classes.py` — HEAD-аас сэргээж сэргэлгүй class-ыг тооцон нэмэх

3. **`&quot;` Jinja-д ажиллахгүй**
   - Migration: `data-confirm="{{ _("...") }}"`-д `&quot;` escape хэрэглэсэн
   - Jinja `{{ _(...) }}` дотор HTML entity escape ажиллахгүй — actual `"` шаардлагатай
   - 5 ширхэг файл template error-той болсон
   - Засвар: single-quote attribute (`data-confirm='{{ _("...") }}'`) болгож сольсон

4. **Linter formatter-ийн хөндлөнгийн тусламж**
   - Зарим засварын дунд template файлуудыг автоматаар formatter (linter) индентлэсэн
   - Migration script-ийн `merge_styles_from_head` хүүхдийн line offset тооцоонд нөлөөлсөн
   - `class=""` attribute давхардаж нэмэгдсэн зарим газар (`<h2 class="text-blue-600" class="...{% if %}...">`)

### 3.3 Шийдэгдээгүй гол асуудал — Navbar items харагдахгүй

**Шинж чанар:**
- 1280×720 desktop browser
- Server-side render зөв (11 nav-item HTML дотор бий) — Python test client-аар баталгаажсан
- Console-д CSP алдаа алга
- Right `<ul>` (notification + admin profile) харагдана
- LEFT `<ul class="navbar-nav me-auto">` (Home/Sample/Equipment гэх мэт меню) **харагдахгүй**

**Шалгасан, асуудал биш:**
- HTML structure (server-side render OK)
- Mobile media query (1280 > 992 тул mobile.css trigger болохгүй)
- Tailwind preflight `* { padding: 0 }` (Bootstrap-ын unlayered selectors win)
- `text-primary`/`text-success` гэх мэт BS class-уудыг Tailwind override хийхгүй
- `<style nonce>` блок дотор `.nav-link` rule зөв байна

**Боломжит шалтгаан** (өнөөдөр шалгаагүй):
- Browser cache (Disable cache + Ctrl+F5)
- `dynamic_styles.js`-ийн MutationObserver Bootstrap dropdown-той зөрчилдөж байж болзошгүй
- Хэрэглэгчийн browser-ийн F12 → Computed style-аар тогтоогдох

**Дараа сесст** хэрэглэгчийн `outerHTML` болон computed style мэдээлэл цуглуулах хэрэгтэй.

### 3.4 Бусад үлдсэн жижиг асуудлууд

- **Gradient class syntax эвдрэл**: `bg-[linear-gradient(135deg,#0ea5e9 0%,#0284c7 100%)]` зэрэгт space хасагдсан → `#0ea5e90%`. Жинхэнэ render-д gradient буруу гарна. ~5 файлд.
- **Давхар `class=""` атрибут**: micro_dashboard.html, water_dashboard.html-ийн `<h2>`-уудад. Browser зөвхөн эхнийхийг л уншина — бусад нь алдагдана.
- **8 ширхэг үлдсэн `tw-` class** JS template literal-ийн дотор. Tailwind generate хийхгүй тул эдгээр зүгээр л dead class.
- **Tracking Prevention warning** — CDN-аас storage хандах browser warning. Sprint 2 (CDN→local bundle)-аар арилна.

### 3.5 Логогийн алдаа

Хэрэглэгч "Energy лого устгах"-ыг хүссэн → 6 байршлаас (base.html, mobile_drawer.html, report.html, pdf_generator.py × 3) `<img>` tag хассан → хэрэглэгч "тэр биш байна, буцаая" гэсэн → бүгдийг буцаасан. **Зорилго тодорхойгүй болсон.**

---

## 4. Файл өөрчлөлт

### Шинээр үүссэн (untracked)
- `package.json`-д Tailwind, autoprefixer, @tailwindcss/cli, @tailwindcss/vite (devDependencies)
- `vite.config.js` — өргөтгөгдсөн
- `src/styles.css` — design tokens + @utility blocks
- `app/utils/vite_assets.py` — Vite manifest helper
- `app/static/js/dynamic_styles.js` — CSP-safe runtime styling
- `scripts/migration/` — 7 ширхэг Python migration script + 4 report файл
- `docs/dev-logs/SESSION_LOG_2026_05_09.md` — энэ файл

### Modified
- `CLAUDE.md` — commit `0224a88` (анхдагч CLAUDE.md үүсгэсэн)
- `app/static/js/csp_handlers.js` — анхны 51 мөрөөс ~140 мөр болж өргөжсөн
- `app/static/js/chat.js` — runtime style injection хассан
- `app/bootstrap/security_headers.py` — CSP3 split (script-src + script-src-elem + script-src-attr + style-src-elem + style-src-attr)
- `app/bootstrap/jinja.py` — vite_* global бүртгэх
- `app/templates/base.html` — Tailwind link, dynamic_styles.js, htmx config meta, navbar item-уудад utility class
- 80+ template — inline style/handler → utility class / data-action
- 5 ширхэг template — `&quot;` → single-quote attribute
- 1 template — `<script nonce="">` нэмсэн (`_sample_disposal_content.html`)

### Untracked architecture docs
- 04-22-нд үүссэн 3 doc хэвээрээ (`ARCHITECTURE_AUDIT/PLAN/PROGRESS_2026_04_22.md`)

### Commit логдсон
- `0224a88` `docs: add CLAUDE.md` (өнөөдөр өглөө)

### Push хийгдсэн
- Үгүй. Бүх ажил локал.

---

## 5. CSP-ийн цэвэрлэгээний явц

**Sprint 1.1c (inline style → class):** ✅ ДУУССАН (1,151 → 0)
**Sprint 1.1b (inline handler → external JS):** ✅ ДУУССАН (140 → 0)
**Sprint 1.1c-runtime (3rd party style mutation):** ⏸ Хойшлуулсан — `style-src-attr 'unsafe-inline'` хэвээр
**Sprint 1.1d (Alpine CSP build):** ⏸ Хойшлуулсан — `'unsafe-eval'` хэвээр
**Sprint 2 (CDN → local bundle):** ⏸ Хойшлуулсан — Tracking Prevention warning хэвээр

---

## 6. Шударга үнэлгээ

**Хийсэн зүйлс:**
- 1,151 inline style + 140 inline handler цэвэрлэсэн (proper фундамент)
- CSP-ийн 4 төрлийн алдаа арилсан (style-src elem/attr, script-src elem/attr)
- Tailwind v4 + Vite суурь босгосон, design system-ийн анх удаа

**Алдаа:**
- prefix(tw) regression-д ~90 минут зарж дараа шийдэл сольсон
- Migration script бэлэн биш байсан, ~378 class дутуу нэмэгдсэн → fix-up хэрэгтэй
- Хэрэглэгчийн төгсгөлд тэмдэглэсэн **navbar items харагдахгүй** асуудлыг шийдэж чадаагүй
- "Зөв шийдэл" зарчмыг хагасчиггүй биелүүлсэн — `'unsafe-eval'`, `style-src-attr 'unsafe-inline'` хэвээр
- Лого устгах хүсэлтийг буруу ойлгож хагас хийгээд буцаасан

**Дүгнэлт:** Технологийн стек шинэчлэгдсэн, foundation босгогдсон, CSP-ийн гурван төрлийн алдаа арилсан. Гэхдээ хэрэглэгчид одоо хүртэл хүлээгдэж буй UI асуудал (navbar items нуугдсан) шийдэгдээгүй. Маргааш заавал эхлэхээс өмнө browser-ийн `outerHTML` болон computed style мэдээлэл цуглуулж шалтгааныг тогтоох.

---

## 7. Дараагийн session-д хийх

1. **Navbar асуудлыг шийдэх** — DevTools мэдээлэл цуглуулах, CSS / JS root cause тогтоох, шийдэх
2. **Жижиг bug-ууд:**
   - Gradient class syntax засах (~5 файл)
   - Давхар `class=""` attr нэгтгэх (2 файл)
   - JS template literal-ийн `tw-` class цэвэрлэх (~8 байршил)
3. **Commit/push стратеги** — өнөөдрийн ажлыг логик commit-уудаар хуваах:
   - feat: Tailwind v4 + Vite + design tokens
   - feat: dynamic_styles.js + csp_handlers.js framework
   - refactor: 1,151 inline style → utility class
   - refactor: 140 inline event handler → data-action
   - feat: CSP3 split (elem/attr) + remove unsafe-inline
4. **Sprint 1.1d** — Alpine CSP build руу шилжих → `'unsafe-eval'` устгах
5. **Sprint 1.1c-runtime** — 3rd party style mutation шалгаж `style-src-attr 'unsafe-inline'` устгах боломжтой эсэхийг үнэлэх
6. **Sprint 2** — CDN → local Vite bundle → Tracking Prevention арилна
