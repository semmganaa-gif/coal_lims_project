# CHANGELOG - 2026-01-12 - Mobile UI + Chemist Report

## Өнөөдрийн ажлууд
1. **Химичийн тайлан** - Шинээр сайжруулсан
2. **Mobile Responsive UI** - 3 хуудсыг mobile-friendly болгосон

---

# ХЭСЭГ 1: ХИМИЧИЙН ТАЙЛАН (Chemist Report)

## 1.0 rank_quality алдаа засвар
**Асуудал**: Зарим химичид `rank_quality` attribute байхгүй байсан тул алдаа гарч байсан.

**Шийдэл** - Default утгууд нэмсэн (`app/routes/report_routes.py`):
```python
chemist_data = {
    'id': user.id,
    'name': _format_short_name(user.name),
    # ... бусад талбарууд
    'rank_total': 0,        # Default нэмсэн
    'rank_quality': 0,      # Default нэмсэн
    'quarterly': 0,         # Default нэмсэн
    'quarterly_growth': 0,  # Default нэмсэн
}
```

Мөн template руу `chemists_by_quality` гэсэн тусдаа sorted list дамжуулсан.

## 1.1 Нэрний формат өөрчлөлт
**Асуудал**: DB-д "GANTULGA Ulziibuyan" гэж хадгалагддаг
**Хүссэн формат**: "Gantulga.U"

**Шийдэл** - `_format_short_name()` функц нэмсэн (`app/routes/report_routes.py`):
```python
def _format_short_name(full_name: str) -> str:
    if not full_name:
        return ""
    parts = full_name.strip().split()
    if len(parts) >= 2:
        first_name = parts[0].capitalize()
        last_name = parts[1]
        return f"{first_name}.{last_name[0].upper()}"
    return full_name
```

## 1.2 Хүснэгтийн багана тэнцүүлэлт
**Асуудал**: Эхний баганууд өргөн, сүүлийнх нь нарийхан

**Шийдэл** - CSS class нэмсэн (`chemist_report.html`):
```css
.chemist-table { table-layout: fixed; width: 100%; }
.chemist-table .col-num { width: 40px; }
.chemist-table .col-name { width: 120px; }
.chemist-table .col-data { width: 70px; }
.chemist-table .col-total { width: 80px; }
```

## 1.3 Эрэмбэлэлт
- **Алдаа tab**: Алдааны тоогоор буурах эрэмбэ (`error_total`, reverse=true)
- **Бусад tab**: Хэвээрээ

## 1.4 Хайлтын цонх хассан
Хэрэглэгчийн хүсэлтээр хайлтын input устгасан.

## 1.5 График таб нэмсэн (Chart.js)
**Шинэ таб**: "График" - 3 график агуулсан:
1. **Сарын шинжилгээ** - Bar chart (химич бүрийн сарын гүйцэтгэл)
2. **Топ 10 химич** - Horizontal bar chart
3. **Алдааны харьцаа** - Doughnut chart

## 1.6 Огнооны хүрээ шүүлт
Header хэсэгт огнооны filter нэмсэн:
```html
<input type="date" name="date_from" class="form-control form-control-sm">
<input type="date" name="date_to" class="form-control form-control-sm">
```

## 1.7 Өмнөх жилтэй харьцуулалт
Сарын график дээр өмнөх жилийн өгөгдлийг overlay болгон харуулсан.

## 1.8 Dashboard хуудас үүсгэсэн
**Шинэ route**: `/reports/dashboard`
**Шинэ template**: `app/templates/reports/dashboard.html`

**Агуулга**:
- 4 KPI card (Дээж, Шинжилгээ, Алдаа, Идэвхтэй ажилтан)
- 6 сарын trend график (Line chart)
- Топ 5 ажилтан (энэ сар)
- Тайлан руу шилжих товчнууд

## 1.9 Consumption тайлан засвар
**Асуудал**: Жил сонгох dropdown-ын сум текст дээр давхцаж байсан
**Шийдэл**: `width: auto` → `width: 90px`

---

# ХЭСЭГ 2: MOBILE RESPONSIVE UI

## Өнөөдрийн зорилго
Гар утас болон таблет дээр LIMS системийг хэрэглэхэд тохиромжтой болгох.
Зөвхөн 3 үндсэн хуудсыг mobile-friendly болгох:
1. Дээж бүртгэл (index)
2. Шинжилгээний хуудас (analysis_page)
3. Ахлахын хяналт (ahlah_dashboard)

**Чухал**: Desktop загвар өөрчлөгдөхгүй байх ёстой.

---

## 1. MOBILE CSS ФАЙЛ ҮҮСГЭСЭН

**Файл**: `app/static/css/mobile.css`

### 1.1 Дээж бүртгэх хуудас (index.html)
```css
@media (max-width: 768px) {
    /* Жагсаалт tab нуух */
    #list-tab, #list-pane { display: none !important; }

    /* Add pane үргэлж харуулах */
    #add-pane { display: block !important; }

    /* Hub grid 2 багана */
    .hub-grid { grid-template-columns: repeat(2, 1fr) !important; }

    /* Nav tabs нуух */
    .nav-tabs { display: none !important; }
}
```

### 1.2 Шинжилгээний хуудас (analysis_page)
```css
@media (max-width: 768px) {
    /* Sidebar нуух */
    .tw-mobile-hide { display: none !important; }

    /* Input font-size 16px (iOS zoom зогсоох) */
    .analysis-input, .form-control, input[type="text"], input[type="number"] {
        font-size: 16px !important;
    }

    /* Action buttons том болгох */
    .btn-save-results { padding: 0.75rem 1rem !important; }
}
```

### 1.3 Ахлахын хяналт (ahlah_dashboard)
```css
@media (max-width: 768px) {
    /* Sidebar нуух */
    .ahlah-sidebar, .metrics-sidebar { display: none !important; }

    /* Action buttons - хүрэхэд амар */
    .btn-action {
        flex: 1 !important;
        padding: 0.75rem 0.5rem !important;
        border-radius: 8px !important;
    }

    /* Stats cards нуух */
    .stats-grid, .chemist-stats-card { display: none !important; }
}
```

---

## 2. MOBILE NAVBAR - АСУУДАЛ БА ШИЙДЭЛ

### 2.1 Анхны асуудал
- Dropdown меню flickering (гялс гялс хийгээд алга болдог)
- Bootstrap-н dropdown болон манай CSS/JS зөрчилдөж байсан

### 2.2 Туршсан шийдлүүд (амжилтгүй)
1. **CSS transition хасах** - Амжилтгүй
2. **JavaScript debounce** - Амжилтгүй
3. **Bootstrap dropdown dispose** - Амжилтгүй
4. **stopImmediatePropagation** - Амжилтгүй
5. **Capture phase event listener** - Амжилтгүй
6. **Accordion style (dropdown үргэлж нээлттэй)** - Амжилтгүй

### 2.3 Эцсийн шийдэл - 3 ШУУД ХОЛБООС
Dropdown бүрэн хасаж, зөвхөн 3 шууд холбоос харуулах:

**CSS (mobile.css)**:
```css
@media (max-width: 991.98px) {
    /* Бүх dropdown болон бусад цэсийг нуух */
    .navbar-collapse .navbar-nav > .nav-item.dropdown,
    .navbar-collapse .navbar-nav > .nav-item:not(.mobile-nav-item) {
        display: none !important;
    }

    /* Mobile-д зөвхөн mobile-nav-item харагдана */
    .navbar-collapse .navbar-nav > .nav-item.mobile-nav-item {
        display: block !important;
    }

    /* Mobile nav items - том, тод */
    .navbar-collapse .mobile-nav-item .nav-link {
        display: block;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f0f0f0;
        border-radius: 8px;
        font-weight: 600;
        color: #333;
    }
}
```

**HTML (base.html)** - 3 nav-item-д `mobile-nav-item` class нэмсэн:
```html
<li class="nav-item mobile-nav-item">
  <a class="nav-link" href="{{ url_for('main.index') }}">
    <i class="bi bi-box-seam me-1 text-primary"></i>Дээж бүртгэл
  </a>
</li>
<li class="nav-item mobile-nav-item">
  <a class="nav-link" href="{{ url_for('analysis.analysis_hub') }}">
    <i class="bi bi-clipboard-data me-1 text-success"></i>Шинжилгээ
  </a>
</li>
<li class="nav-item mobile-nav-item">
  <a class="nav-link" href="{{ url_for('analysis.ahlah_dashboard') }}">
    <i class="bi bi-shield-check me-1 text-warning"></i>Ахлахын хяналт
  </a>
</li>
```

---

## 3. BASE.HTML ӨӨРЧЛӨЛТҮҮД

### 3.1 Mobile CSS холбосон
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/mobile.css') }}?v=10">
```

### 3.2 Inline mobile стилүүд хассан
base.html дотор байсан `@media (max-width: 768px)` стилүүдийг устгаж, mobile.css руу шилжүүлсэн.

**Устгасан код (line 121-182)**:
```css
/* ========== MOBILE RESPONSIVE STYLES ========== */
@media (max-width: 768px) {
    .navbar-collapse { position: fixed; ... }
    ...
}
```

Оронд нь:
```css
/* Mobile стилүүд mobile.css файлд байна */
```

### 3.3 Debug script нэмсэн
```javascript
<!-- Mobile debug -->
<script>
  document.addEventListener('DOMContentLoaded', function() {
    var nav = document.getElementById('mainNavbar');
    if (nav) {
      nav.addEventListener('show.bs.collapse', function() { console.log('NAVBAR SHOW'); });
      nav.addEventListener('shown.bs.collapse', function() { console.log('NAVBAR SHOWN'); });
      nav.addEventListener('hide.bs.collapse', function() { console.log('NAVBAR HIDE'); });
      nav.addEventListener('hidden.bs.collapse', function() { console.log('NAVBAR HIDDEN'); });
    }
  });
</script>
```

### 3.4 Nav item text өөрчлөлт
- "Нүүр" → "Дээж бүртгэл" (илүү тодорхой)

---

## 4. ANALYSIS_PAGE.HTML ӨӨРЧЛӨЛТҮҮД

### 4.1 Mobile дээр Дээж товч нэмсэн
Өмнө нь mobile дээр зөвхөн "Хадгалах" товч байсан.

**Хуучин код**:
```html
{# Mobile: Зөвхөн Хадгалах товч #}
{% if not is_mass_page %}
<button class="btn btn-success btn-sm d-md-none" id="save-analysis-results-mobile">
  <i class="bi bi-check-lg"></i>
</button>
{% endif %}
```

**Шинэ код**:
```html
{# Mobile: Дээж + Хадгалах товч #}
<div class="d-md-none d-flex gap-2">
  <button class="btn btn-outline-primary btn-sm" data-bs-toggle="modal" data-bs-target="#selectSamplesModal">
    <i class="bi bi-plus-circle"></i> Дээж
  </button>
  {% if not is_mass_page %}
  <button class="btn btn-success btn-sm" id="save-analysis-results-mobile" data-action="save-results">
    <i class="bi bi-check-lg"></i> Хадгалах
  </button>
  {% endif %}
</div>
```

---

## 5. AG GRID - ТООН KEYBOARD

### 5.1 Асуудал
Mobile дээр шинжилгээний үр дүн оруулахад үсгэн keyboard гарч байсан.

### 5.2 Шийдэл
`app/static/js/aggrid_helpers.js` файлд `inputmode="decimal"` нэмсэн:

**baseGridOptions-д нэмсэн**:
```javascript
onCellEditingStarted: function(params) {
  if (window.innerWidth < 992) {
    setTimeout(function() {
      var input = params.api.getCellEditorInstances()[0]?.getGui()?.querySelector('input');
      if (input && (input.type === 'text' || input.type === 'number')) {
        input.setAttribute('inputmode', 'decimal');
      }
    }, 10);
  }
},
```

**Global fallback нэмсэн**:
```javascript
// Mobile: AG Grid дотор input focus хийхэд тоон keyboard харуулах
if (w.innerWidth < 992) {
  document.addEventListener('focusin', function(e) {
    var input = e.target;
    if (input.tagName === 'INPUT' && input.closest('.ag-cell-editor')) {
      if (!input.hasAttribute('inputmode')) {
        input.setAttribute('inputmode', 'decimal');
      }
    }
  }, true);
  console.log('📱 Mobile numeric keyboard enabled for AG Grid inputs');
}
```

---

## 6. ФАЙЛЫН ХУВИЛБАРУУД (CACHE BUST)

| Файл | Хуучин | Шинэ |
|------|--------|------|
| mobile.css | v1 | v10 |
| aggrid_helpers.js | v3 | v4 |

---

## 7. УСТГАСАН / ХЯЛБАРШУУЛСАН КОД

### 7.1 Устгасан JavaScript
Dropdown toggle-тэй холбоотой олон JS код туршиж үзээд эцэст нь бүгдийг устгасан:
- Bootstrap dropdown dispose
- Custom click handlers
- Capture phase event listeners
- Debounce logic

### 7.2 Үлдсэн JavaScript
Зөвхөн debug logging:
```javascript
nav.addEventListener('show.bs.collapse', function() { console.log('NAVBAR SHOW'); });
```

---

## 8. ТЕСТ ХИЙГДСЭН

### 8.1 Mobile дээр тест
- [x] Hamburger меню нээгдэх/хаагдах
- [x] 3 шууд холбоос харагдах
- [x] Дээж бүртгэл хуудас руу орох
- [x] Шинжилгээний хуудас руу орох
- [x] Дээж нэмэх modal нээгдэх
- [x] Тоон keyboard гарах
- [x] Ахлахын хяналт руу орох

### 8.2 Desktop дээр тест
- [x] Бүх dropdown меню ажиллах
- [x] Хуучин загвар хэвээрээ

---

## 9. МЭДЭГДЭХ ЗҮЙЛС

### 9.1 Breakpoint
- Bootstrap navbar: `navbar-expand-lg` = 992px
- Mobile CSS: `max-width: 991.98px`
- Зарим хуудсын CSS: `max-width: 768px`

### 9.2 Давхар base.html
Төсөлд 2 base.html файл байна:
1. `D:\coal_lims_project\app\templates\base.html` - **ИДЭВХТЭЙ**
2. `D:\coal_lims_project\coal_lims_project\app\templates\base.html` - Хуучин backup

### 9.3 tw-mobile-hide class
Tailwind CSS-ээс ирсэн class. Analysis page дээр sidebar нуухад ашиглагдаж байна.

---

## 10. ДҮГНЭЛТ

### Амжилттай хийгдсэн
1. Mobile navbar - 3 шууд холбоос
2. Дээж бүртгэл хуудас - жагсаалт нуусан, form харуулсан
3. Шинжилгээний хуудас - Дээж товч нэмсэн, тоон keyboard
4. Desktop загвар - өөрчлөгдөөгүй

### Сургамж
- Bootstrap dropdown + fixed position navbar = асуудалтай
- Энгийн шийдэл (3 шууд холбоос) илүү найдвартай
- `inputmode="decimal"` нь mobile тоон keyboard-д хамгийн сайн

---

---

# ХЭСЭГ 3: ӨӨРЧЛӨГДСӨН ФАЙЛУУДЫН ЖАГСААЛТ

## Python файлууд
| Файл | Өөрчлөлт |
|------|----------|
| `app/routes/report_routes.py` | `_format_short_name()` функц, dashboard route, chemist_report сайжруулалт |

## HTML Templates
| Файл | Өөрчлөлт |
|------|----------|
| `app/templates/base.html` | mobile-nav-item class, mobile.css холбоос, debug script, nav text |
| `app/templates/reports/chemist_report.html` | График tab, огнооны filter, багана CSS, хайлт хассан |
| `app/templates/reports/dashboard.html` | **ШИНЭ** - KPI cards, charts |
| `app/templates/reports/consumption.html` | Жил select width засвар |
| `app/templates/analysis_page.html` | Mobile дээр Дээж товч нэмсэн |

## CSS файлууд
| Файл | Өөрчлөлт |
|------|----------|
| `app/static/css/mobile.css` | **ШИНЭ/САЙЖРУУЛСАН** - Бүх mobile стилүүд |

## JavaScript файлууд
| Файл | Өөрчлөлт |
|------|----------|
| `app/static/js/aggrid_helpers.js` | Mobile тоон keyboard (`inputmode="decimal"`) |

---

# ХЭСЭГ 4: ТОХИРГООНЫ ХУВИЛБАРУУД

```
mobile.css      v1  → v10
aggrid_helpers.js   v3  → v4
custom.css      v9  (өөрчлөгдөөгүй)
```

---

# ХЭСЭГ 5: ЦААШИД ХИЙХ ЗҮЙЛС (TODO)

1. [ ] Mobile drawer sidebar (analysis page-д quick ref, timer)
2. [ ] Offline горим (PWA)
3. [ ] Push notification

---

**Бичсэн**: Claude Code
**Огноо**: 2026-01-12
**Хувилбар**: v10
**Нийт өөрчлөгдсөн файл**: 8+
