/* ===============================
 * 1) Review data renderer (raw_data) - Parallel table display
 * =============================== */
const DEFAULT_PARALLEL_SCHEMA = {
  title: "Parallel Measurements",
  columns: [
    { key: "label", label: "#" },
    { key: "m1", label: "m1", format: "float", precision: 4 },
    { key: "m2", label: "m2", format: "float", precision: 4 },
    { key: "m3", label: "m3", format: "float", precision: 4 },
    { key: "result", label: "Result", format: "float", precision: 3 }
  ]
};

const SUMMARY_FIELDS = [
  { key: "avg", label: "Average", format: "float", precision: 3 },
  { key: "diff", label: "Tolerance (T)", format: "float", precision: 3 },
  { key: "result", label: "Result", format: "float", precision: 3 },
  { key: "final_result", label: "Final Result", format: "float", precision: 3 },
  { key: "A", label: "A (tray+sample)", format: "float", precision: 3 },
  { key: "B", label: "B (tray)", format: "float", precision: 3 },
  { key: "C", label: "C (residue)", format: "float", precision: 3 },
  { key: "weight", label: "Weight", format: "float", precision: 3 },
  { key: "limit_used", label: "Limit", format: "float", precision: 3 },
  { key: "limit_mode", label: "Limit Mode" },
  { key: "t_exceeded", label: "T Exceeded", format: "boolean" },
  { key: "retest_mode", label: "Retest Mode" },
  { key: "is_low_avg", label: "Low Result?", format: "boolean" }
];

function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function getParallelSchema(code) {
  const map = window.ANALYSIS_SCHEMAS || {};
  const normalized = (code || "").trim();
  const upper = normalized.toUpperCase();
  const schema =
    map[normalized] ||
    map[upper] ||
    map._default ||
    {};
  const parallels = schema.parallels || {};
  const columns =
    Array.isArray(parallels.columns) && parallels.columns.length
      ? parallels.columns
      : DEFAULT_PARALLEL_SCHEMA.columns;
  const title = parallels.title || DEFAULT_PARALLEL_SCHEMA.title;
  return { title, columns };
}

function formatValue(value, cfg) {
  if (value === null || value === undefined || value === "") return "-";
  const format = cfg && cfg.format;
  if (format === "float") {
    const digits = typeof cfg.precision === "number" ? cfg.precision : 2;
    const num = Number(value);
    if (Number.isFinite(num)) return num.toFixed(digits);
    return escapeHtml(value);
  }
  if (format === "boolean") {
    return value ? "Yes" : "No";
  }
  return escapeHtml(value);
}

function deriveParallels(raw) {
  if (!raw || typeof raw !== 'object') return [];

  // 1. Хэрэв parallels массив байвал түүнийг ашиглах
  if (Array.isArray(raw.parallels) && raw.parallels.length) {
    return raw.parallels;
  }

  const rows = [];

  // 2. p1, p2, p3 бүтэц (хамгийн түгээмэл)
  ["p1", "p2", "p3"].forEach((key) => {
    const val = raw[key];
    if (val && typeof val === "object" && Object.keys(val).length) {
      // num талбарыг label болгож хувиргах
      const row = { label: key.toUpperCase(), ...val };
      if (val.num) {
        row.label = val.num;
      }
      rows.push(row);
    }
  });

  // 3. Хэрэв p1/p2 байхгүй бол шууд raw дотроос хайх
  if (rows.length === 0) {
    // m1, m2, m3, result талбар байвал нэг мөр болгоно
    if (raw.m1 !== undefined || raw.m2 !== undefined || raw.result !== undefined) {
      rows.push({ label: '1', ...raw });
    }
  }

  // 4. FM (Free Moisture) шинжилгээний талбарууд
  if (rows.length === 0 && (raw.before_g !== undefined || raw.after_g !== undefined || raw.loss_g !== undefined)) {
    rows.push({
      label: 'FM',
      m1: raw.tray_g,
      m2: raw.before_g,
      m3: raw.after_g,
      result: raw.loss_g || raw.fm_pct
    });
  }

  // 5. CV шинжилгээ - q1, q2 талбарууд
  if (rows.length === 0 && (raw.q1 !== undefined || raw.q2 !== undefined)) {
    if (raw.q1 !== undefined) rows.push({ label: 'Q1', result: raw.q1 });
    if (raw.q2 !== undefined) rows.push({ label: 'Q2', result: raw.q2 });
  }

  // 6. MG tube (Соронзон) — empty_crucible, sample_mass, dried_weight
  if (rows.length === 0 && (raw.empty_crucible !== undefined || raw.mg_mass !== undefined)) {
    rows.push({
      label: 'MG',
      empty_crucible: raw.empty_crucible,
      sample_mass: raw.sample_mass,
      dried_weight: raw.dried_weight,
      mg_mass: raw.mg_mass,
      nomg_mass: raw.nomg_mass,
      mg_pct: raw.mg_pct
    });
  }

  // 7. MG_SIZE (Ширхэглэл) — fractions массив
  if (rows.length === 0 && Array.isArray(raw.fractions) && raw.fractions.length) {
    raw.fractions.forEach(function(f) {
      rows.push({
        label: f.label || '',
        m2: f.m2,
        m3: f.m3,
        m1: f.m1,
        pct: f.pct
      });
    });
  }

  return rows;
}

function renderParallelTable(parallels, schema) {
  if (!parallels.length) return "";
  const columns = schema.columns || DEFAULT_PARALLEL_SCHEMA.columns;
  const header = columns
    .map((col) => {
      const label = escapeHtml(col.label || col.key || "");
      const unit = col.unit
        ? `<small class="text-muted ms-1">${escapeHtml(col.unit)}</small>`
        : "";
      return `<th style="padding:6px 10px; font-size:0.75rem; background:#f1f5f9; white-space:nowrap;">${label}${unit}</th>`;
    })
    .join("");
  const body = parallels
    .map((row, idx) => {
      const rowBg = idx % 2 === 0 ? '#fff' : '#f8fafc';
      const cells = columns
        .map((col) => {
          const val = formatValue(row && row[col.key], col);
          const isNum = col.key === 'label' || col.key === 'num';
          const style = isNum
            ? 'font-weight:600; color:#6366f1;'
            : 'font-family:Consolas,monospace;';
          return `<td style="padding:5px 8px; ${style}">${val}</td>`;
        })
        .join("");
      return `<tr style="background:${rowBg};">${cells}</tr>`;
    })
    .join("");
  return `
    <div class="table-responsive mb-2" style="border-radius:8px; overflow:hidden; border:1px solid #e2e8f0;">
      <table class="table table-sm align-middle text-center mb-0" style="margin:0;">
        <thead><tr>${header}</tr></thead>
        <tbody>${body}</tbody>
      </table>
    </div>`;
}

function buildSummarySection(raw, rowCtx) {
  if (!raw || typeof raw !== "object") raw = {};
  const segments = [];
  const seen = new Set();

  function append(label, value, cfg, highlight) {
    if (value === undefined || value === null || value === "") return;
    const key = `${label}-${cfg?.key || label}`;
    if (seen.has(key)) return;
    seen.add(key);
    const valueClass = highlight ? 'fw-bold text-success' : 'fw-semibold';
    segments.push(
      `<div class="d-flex justify-content-between py-1">
        <span class="text-muted">${escapeHtml(label)}</span>
        <span class="${valueClass}">${formatValue(value, cfg)}</span>
      </div>`
    );
  }

  // Дундаж ба тохирц (хамгийн чухал)
  append("Average", raw.avg, { format: "float", precision: 3 }, true);
  append("Tolerance (T)", raw.diff, { format: "float", precision: 3 });

  // Бусад SUMMARY_FIELDS (avg, diff-ээс бусад)
  SUMMARY_FIELDS.forEach((cfg) => {
    if (cfg.key !== 'avg' && cfg.key !== 'diff') {
      append(cfg.label, raw[cfg.key], cfg);
    }
  });

  // Row context-оос авах fallback утгууд
  const fallbackFields = [
    { key: "final_value", label: "Final Result", format: "float", precision: 3 },
    { key: "t_value", label: "Tolerance (T)", format: "float", precision: 3 },
  ];

  fallbackFields.forEach((cfg) => {
    const value =
      raw[cfg.key] !== undefined && raw[cfg.key] !== null && raw[cfg.key] !== ""
        ? raw[cfg.key]
        : rowCtx?.[cfg.key];
    append(cfg.label, value, cfg);
  });

  if (!segments.length) return "";
  return `<div class="bg-light border rounded p-2 mt-2 small">${segments.join("")}</div>`;
}

function buildRawJsonSection(raw) {
  if (!raw || typeof raw !== "object" || !Object.keys(raw).length) return "";
  let jsonStr = "";
  try {
    jsonStr = JSON.stringify(raw, null, 2);
  } catch (err) {
    return "";
  }
  return `<details class="mt-2 small">
    <summary class="text-muted">Raw snapshot</summary>
    <pre class="mb-0" style="white-space:pre-wrap;font-size:0.75rem;">${escapeHtml(jsonStr)}</pre>
  </details>`;
}

// MG tube, MG_SIZE-д зориулсан тусгай schema
const MG_PARALLEL_SCHEMAS = {
  'MG_MT': {
    title: 'MG Moisture Test',
    columns: [
      { key: 'label', label: '#' },
      { key: 'm1', label: 'Бортого(g)', format: 'float', precision: 4 },
      { key: 'm2', label: 'Дээж(g)', format: 'float', precision: 4 },
      { key: 'm3', label: 'Хатаасан(g)', format: 'float', precision: 4 },
      { key: 'result', label: 'MT%', format: 'float', precision: 2 }
    ]
  },
  'MG_TRD': {
    title: 'MG True Relative Density',
    columns: [
      { key: 'label', label: '#' },
      { key: 'pycno', label: 'Пикнометр', format: 'float', precision: 0 },
      { key: 'm', label: 'm(g)', format: 'float', precision: 4 },
      { key: 'm2', label: 'm2(g)', format: 'float', precision: 4 },
      { key: 'm1', label: 'm1(g)', format: 'float', precision: 4 },
      { key: 'result', label: 'TRD', format: 'float', precision: 3 }
    ]
  },
  'MG': {
    title: 'Magnetic Fraction',
    columns: [
      { key: 'label', label: '#' },
      { key: 'empty_crucible', label: 'Хоосон(g)', format: 'float', precision: 2 },
      { key: 'sample_mass', label: 'Дээж(g)', format: 'float', precision: 1 },
      { key: 'dried_weight', label: 'Хатаасан(g)', format: 'float', precision: 2 },
      { key: 'mg_mass', label: 'MG(g)', format: 'float', precision: 2 },
      { key: 'nomg_mass', label: 'NoMG(g)', format: 'float', precision: 2 },
      { key: 'mg_pct', label: 'MG%', format: 'float', precision: 2 }
    ]
  },
  'MG_TUBE': {
    title: 'Magnetic Fraction',
    columns: [
      { key: 'label', label: '#' },
      { key: 'empty_crucible', label: 'Хоосон(g)', format: 'float', precision: 2 },
      { key: 'sample_mass', label: 'Дээж(g)', format: 'float', precision: 1 },
      { key: 'dried_weight', label: 'Хатаасан(g)', format: 'float', precision: 2 },
      { key: 'mg_mass', label: 'MG(g)', format: 'float', precision: 2 },
      { key: 'nomg_mass', label: 'NoMG(g)', format: 'float', precision: 2 },
      { key: 'mg_pct', label: 'MG%', format: 'float', precision: 2 }
    ]
  },
  'MG_SIZE': {
    title: 'Size Distribution',
    columns: [
      { key: 'label', label: 'Fraction' },
      { key: 'm2', label: 'm2(g)', format: 'float', precision: 1 },
      { key: 'm3', label: 'm3(g)', format: 'float', precision: 1 },
      { key: 'm1', label: 'g', format: 'float', precision: 1 },
      { key: 'pct', label: '%', format: 'float', precision: 1 }
    ]
  }
};

function ReviewDataRenderer(params) {
  const raw = params.data.raw_data || {};
  const rowCtx = params.data || {};
  const code = rowCtx.analysis_code || "";
  const codeUpper = code.toUpperCase();
  const schema = MG_PARALLEL_SCHEMAS[code] || MG_PARALLEL_SCHEMAS[codeUpper] || getParallelSchema(code);
  const parallels = deriveParallels(raw);
  const summaryBlock = buildSummarySection(raw, rowCtx);
  const hasSummary = Boolean(summaryBlock);

  // Debug - console дээр харуулах
  logger.debug('ReviewDataRenderer:', code, 'raw_data:', JSON.stringify(raw), 'parallels:', parallels.length);

  // raw object-ын бодит утгууд (p1, p2, parallels гэх мэт - _schema-аас бусад)
  const meaningfulKeys = Object.keys(raw).filter(k => k !== '_schema' && raw[k] !== null && raw[k] !== undefined && raw[k] !== '');
  const hasRaw = meaningfulKeys.length > 0;

  // DOM element үүсгэх (AG Grid шаардлага)
  const container = document.createElement('div');
  container.className = 'review-data-cell';
  container.style.cssText = 'font-size:0.85em; padding:8px 0;';

  // Parallel хүснэгт харуулах
  if (parallels.length) {
    const titleDiv = document.createElement('div');
    titleDiv.className = 'text-muted small fw-semibold mb-1';
    titleDiv.textContent = schema.title;
    container.appendChild(titleDiv);

    const tableHtml = renderParallelTable(parallels, schema);
    const tableWrapper = document.createElement('div');
    tableWrapper.innerHTML = tableHtml;
    container.appendChild(tableWrapper);
  }

  // Summary section - avg, diff, result гэх мэт
  if (hasSummary) {
    const summaryWrapper = document.createElement('div');
    summaryWrapper.innerHTML = summaryBlock;
    container.appendChild(summaryWrapper);
  }

  // Хэрэв parallel ч, summary ч байхгүй бол raw JSON харуулах
  if (!parallels.length && !hasSummary && hasRaw) {
    const displayRaw = {};
    meaningfulKeys.forEach(k => { displayRaw[k] = raw[k]; });
    const pre = document.createElement('pre');
    pre.className = 'raw-json-box small mb-0';
    pre.style.cssText = 'white-space:pre-wrap; background:#f8fafc; padding:8px; border-radius:6px; max-height:120px; overflow:auto;';
    pre.textContent = JSON.stringify(displayRaw, null, 2);
    container.appendChild(pre);
  }

  // Raw data байвал "Raw snapshot" details нэмэх
  if ((parallels.length || hasSummary) && hasRaw) {
    const detailsHtml = buildRawJsonSection(raw);
    if (detailsHtml) {
      const detailsWrapper = document.createElement('div');
      detailsWrapper.innerHTML = detailsHtml;
      container.appendChild(detailsWrapper);
    }
  }

  // Хоосон байвал
  if (!parallels.length && !hasSummary && !hasRaw) {
    const emptySpan = document.createElement('span');
    emptySpan.className = 'text-muted small';
    emptySpan.textContent = 'No raw data';
    container.appendChild(emptySpan);
  }

  return container;
}

function updateDashboardMetrics(rows) {
  const stats = {
    total: rows.length,
    pending: 0,
    flagged: 0,
  };

  rows.forEach((row) => {
    const status = row.status;
    if (status === "pending_review") stats.pending += 1;
    const needsRetest =
      status === "rejected" ||
      row.error_reason === "GI_RETEST_3_3" ||
      (row.raw_data &&
        (row.raw_data.retest_mode === "3_3" ||
          row.raw_data.is_low_avg === true));
    if (needsRetest) stats.flagged += 1;
  });

  const assignText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  };

  assignText("metric-total", stats.total);
  assignText("metric-pending", stats.pending);
  assignText("metric-rejected", stats.flagged);

  const refreshEl = document.getElementById("metrics-refresh");
  if (refreshEl) {
    const now = new Date();
    refreshEl.textContent =
      "Last updated: " +
      now.toLocaleString("en-US", { hour12: false });
  }
}
/* ===============================
 * 2) Actions renderer (approve / reject)
 * =============================== */
function ActionsRenderer(params) {
  const resultId = escapeHtml(params.data.result_id);
  const sampleCode = escapeHtml(params.data.sample_code);
  const analysisName = escapeHtml(params.data.analysis_name);

  const approveBtn = `
    <button type="button" class="btn btn-success btn-sm w-100 mb-1 btn-approve" data-id="${resultId}">
      <i class="bi bi-check-circle"></i> Approve
    </button>
  `;

  const rejectBtn = `
    <button type="button" class="btn btn-outline-danger btn-sm w-100 btn-open-reject-modal"
      data-bs-toggle="modal" data-bs-target="#rejectModal"
      data-result-id="${resultId}" data-sample-code="${sampleCode}" data-analysis-name="${analysisName}">
      <i class="bi bi-x-circle"></i> Reject
    </button>
  `;
  return `<div class="d-flex flex-column gap-1 p-1">${approveBtn}${rejectBtn}</div>`;
}

/* ===============================
 * 3) AG Grid options
 * =============================== */
const gridOptions = {
  theme: "legacy",  // AG Grid v34+ - use legacy CSS theme
  columnDefs: [
    {
      headerName: "Sample / Analysis",
      cellRenderer: params => {
        const p = params.data;
        const status = p.status;
        const errorReason = p.error_reason;
        const raw = p.raw_data || {};
        const isGiRetest = (
          (p.analysis_code === 'Gi') &&
          (
            errorReason === 'GI_RETEST_3_3' ||
            raw.retest_mode === '3_3' ||
            raw.is_low_avg === true
          )
        );
        let badge = '';

        if (status === 'rejected' && isGiRetest) {
           badge = `<div class="mt-1"><span class="badge bg-warning text-dark text-wrap text-start" style="line-height:1.3; font-weight:normal;">
                      <i class="bi bi-arrow-repeat"></i> 3:3 Retest
                    </span></div>`;
        } else if (status === 'rejected') {
           // window.ERROR_LABELS нь дээд талд тодорхойлогдсон map
           const reasonText = window.ERROR_LABELS[errorReason] || errorReason || 'Rejected';
           badge = `<div class="mt-1"><span class="badge bg-danger text-wrap text-start" style="line-height:1.3; font-weight:normal;">
                      <i class="bi bi-exclamation-triangle-fill"></i> ${escapeHtml(reasonText)}
                    </span></div>`;
        } else if (status === 'pending_review') {
           badge = '<span class="badge bg-warning text-dark ms-1">Pending</span>';
        }

        return `<div class="d-flex flex-column py-1">
                  <span class="fw-bold text-primary" style="font-size:0.95rem;">${escapeHtml(p.sample_code)}</span>
                  <small class="text-muted fw-semibold">${escapeHtml(p.analysis_name)}</small>
                  ${badge}
                </div>`;
      },
      filter: true,
      floatingFilter: true,
      minWidth: 260,
      autoHeight: true,
      wrapText: true,
      cellStyle: { 'white-space': 'normal' }
    },
    {
      headerName: "Calculation Data (Raw Data)",
      cellRenderer: ReviewDataRenderer,
      autoHeight: true,
      wrapText: true,
      minWidth: 450,
      flex: 2,
      cellStyle: { 'white-space': 'normal', 'line-height': '1.4' }
    },
    {
      headerName: "T",
      field: "t_value",
      width: 80,
      cellStyle: {textAlign: 'center', fontWeight: 'bold', verticalAlign: 'middle'},
      valueFormatter: p => (p.value != null) ? Number(p.value).toFixed(3) : '-'
    },
    {
      headerName: "Final Result",
      field: "final_value",
      width: 120,
      cellStyle: {textAlign: 'right', fontWeight: 'bold', color: '#198754', verticalAlign: 'middle', fontSize:'1.1em'},
      valueFormatter: p => (p.value != null) ? Number(p.value).toFixed(3) : '-'
    },
    {
      headerName: "Analyst / Date",
      cellRenderer: p => `
        <div class="small lh-sm py-1">
          <div class="fw-bold"><i class="bi bi-person-circle"></i> ${escapeHtml(p.data.user_name)}</div>
          <div class="text-muted" style="font-size:0.75rem;">${escapeHtml(p.data.updated_at)}</div>
        </div>`,
      width: 170,
      cellStyle: {verticalAlign: 'middle'}
    },
    {
      headerName: "Actions",
      cellRenderer: ActionsRenderer,
      width: 140,
      pinned: 'right',
      cellStyle: {display: 'flex', alignItems: 'center', justifyContent: 'center'}
    }
  ],
  rowData: [],
  rowHeight: null,
  suppressRowTransform: true,
  getRowHeight: function(params) {
    // AutoHeight - let grid calculate based on content
    return null;
  },
  defaultColDef: {
    resizable: true,
    sortable: true,
    filter: true,
    suppressHeaderMenuButton: true,
    floatingFilterComponentParams: { suppressFilterButton: true },
    wrapText: true,
    autoHeight: true
  },
  // Ensure grid resizes properly
  onGridReady: function(params) {
    params.api.sizeColumnsToFit();
  },
  onFirstDataRendered: function(params) {
    params.api.sizeColumnsToFit();
  }
};

/* ===============================
 * 4) Grid-ийг ачаалах
 * =============================== */
document.addEventListener("DOMContentLoaded", () => {
  const gridDiv = document.querySelector("#myGrid");
  const gridApi = agGrid.createGrid(gridDiv, gridOptions);

  const urlParams = new URLSearchParams(window.location.search);
  const apiUrl = `/api/ahlah_data?${urlParams.toString()}`;

  fetch(apiUrl)
    .then(response => response.json())
    .then(data => {
      gridApi.setGridOption('rowData', data);
      updateDashboardMetrics(data);
    })
    .catch(error => {
      logger.error('Grid data load error:', error);
      gridDiv.innerHTML = '<div class="alert alert-danger m-3">Өгөгдөл ачаалахад алдаа гарлаа.</div>';
    });

  // Approve Button Listener
  document.addEventListener('click', function(e) {
    if (e.target.closest('.btn-approve')) {
        const btn = e.target.closest('.btn-approve');
        const id = btn.dataset.id;
        if(!confirm("Энэ үр дүнг зөвшөөрөх үү?")) return;

        btn.disabled = true;
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
        fetch(`/api/update_result_status/${id}/approved`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken }
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
          if (data.message === 'OK') {
            location.reload();
          } else {
            alert(data.message || 'Алдаа гарлаа');
            btn.disabled = false;
          }
        })
        .catch(function(err) {
          logger.error('Approve error:', err);
          alert('Сүлжээний алдаа');
          btn.disabled = false;
        });
    }
  });
});

/* ===============================
 * 5) Modal logic (reject)
 * =============================== */
$(document).on('click', '.btn-open-reject-modal', function () {
  $('#reject-result-id').val($(this).data('result-id'));
  const analysisName = $(this).data('analysis-name') || '';
  $('#reject-sample-info').text($(this).data('sample-code') + ' / ' + analysisName);

  // Reset form
  $('#rejection_category').val('');
});

$('#reject-form').on('submit', function (e) {
  e.preventDefault();

  const id  = $('#reject-result-id').val();
  const cat = $('#rejection_category').val();

  // ✅ ШИНЭЧЛЭЛ: Коммент бичдэг хэсэг байхгүй болсон тул
  // Сонгосон сонголтын текстийг (жишээ нь "1. Дээж бэлтгэл...") коммент болгож авна.
  const comment = $('#rejection_category option:selected').text();

  if (!id || !cat) {
    alert('Буцаах шалтгаанаа сонгоно уу.');
    return;
  }

  const $btn = $(this).find('button[type="submit"]');
  $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> Боловсруулж байна...');

  const csrfToken = $('meta[name="csrf-token"]').attr('content') || '';
  $.ajax({
    url: '/api/update_result_status/' + id + '/rejected',
    method: 'POST',
    contentType: 'application/json',
    headers: { 'X-CSRFToken': csrfToken },
    data: JSON.stringify({
      rejection_category: cat,
      rejection_comment:  comment, // Сонголтын текстийг коммент болгож явуулна
      error_reason:       cat,
      action_type:        'reject_only'
    }),
    success: function () {
      const m = bootstrap.Modal.getInstance(document.getElementById('rejectModal'));
      if (m) m.hide();
      location.reload();
    },
    error: function (xhr) {
      alert(xhr.responseJSON?.message || 'Алдаа гарлаа');
      $btn.prop('disabled', false).text('Буцаах');
    }
  });
});
// app/static/js/ahlah_dashboard.js

// ... чиний AG Grid / бусад код байна ... 

function loadAhlahKpiSummary() {
  if (!window.AHLAH_KPI_SUMMARY_URL) return;

  fetch(window.AHLAH_KPI_SUMMARY_URL, {
    headers: { 'Accept': 'application/json' }
  })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (!data) return;

      // Ээлжийн буцаалт (KPI)
      var shiftSpan = document.getElementById('kpi-shift-total');
      if (shiftSpan && data.shift) {
        shiftSpan.textContent = data.shift.total_errors ?? 0;
      }

      // Сүүлийн 14 хоногийн буцаалт (KPI)
      var d14Span = document.getElementById('kpi-14d-total');
      if (d14Span && data.days14) {
        d14Span.textContent = data.days14.total_errors ?? 0;
      }
    })
    .catch(function (err) {
      logger.error('KPI summary load failed:', err);
    });
}

// Аль хэдийн өөр DOMContentLoaded listener байж болно – давхар байхад асуудалгүй.
document.addEventListener('DOMContentLoaded', function () {
  loadAhlahKpiSummary();
  loadAhlahStats();
});

/* ===============================
 * Химич болон Шинжилгээний статистик ачаалах
 * =============================== */
function loadAhlahStats() {
  if (!window.AHLAH_STATS_URL) return;

  fetch(window.AHLAH_STATS_URL, {
    headers: { 'Accept': 'application/json' }
  })
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (!data) return;

      // Metric cards шинэчлэх (summary)
      if (data.summary) {
        const total = document.getElementById('metric-total');
        const approved = document.getElementById('metric-approved');
        const pending = document.getElementById('metric-pending');
        const rejected = document.getElementById('metric-rejected');

        if (total) total.textContent = data.summary.total || 0;
        if (approved) approved.textContent = data.summary.approved || 0;
        if (pending) pending.textContent = data.summary.pending || 0;
        if (rejected) rejected.textContent = data.summary.rejected || 0;
      }

      // Химичийн статистик
      renderChemistStats(data.chemists || []);

      // Шинжилгээний төрөл статистик
      renderAnalysisStats(data.analysis_types || []);

      // Шинэчлэгдсэн цаг
      const refreshEl = document.getElementById('metrics-refresh');
      if (refreshEl) {
        const now = new Date();
        refreshEl.textContent = 'Updated: ' + now.toLocaleString('en-US', { hour12: false });
      }
    })
    .catch(function(err) {
      logger.error('Ahlah stats load failed:', err);
    });
}

function renderChemistStats(chemists) {
  const container = document.getElementById('chemist-stats-list');
  const badge = document.getElementById('chemist-total-badge');

  if (!container) return;

  if (badge) {
    badge.textContent = chemists.length + ' chemists';
  }

  if (chemists.length === 0) {
    container.innerHTML = `
      <div class="stats-empty">
        <i class="bi bi-inbox"></i>
        No analyses performed today
      </div>
    `;
    return;
  }

  let html = '';
  chemists.forEach(function(c, idx) {
    // Use first 2 characters of name as avatar
    const initials = (c.username || 'XX').substring(0, 2).toUpperCase();

    html += `
      <div class="stats-item">
        <div class="stats-item-name">
          <div class="stats-item-avatar">${initials}</div>
          <span>${escapeHtml(c.username)}</span>
        </div>
        <div class="stats-item-counts">
          <span class="stats-count total" title="Total">${c.total}</span>
          <span class="stats-count approved" title="Approved">${c.approved}</span>
          <span class="stats-count pending" title="Pending">${c.pending}</span>
          ${c.rejected > 0 ? `<span class="stats-count rejected" title="Rejected">${c.rejected}</span>` : ''}
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function renderAnalysisStats(analysisTypes) {
  const container = document.getElementById('analysis-stats-list');
  const badge = document.getElementById('analysis-total-badge');

  if (!container) return;

  if (badge) {
    badge.textContent = analysisTypes.length + ' types';
  }

  if (analysisTypes.length === 0) {
    container.innerHTML = `
      <div class="stats-empty">
        <i class="bi bi-inbox"></i>
        No analyses today
      </div>
    `;
    return;
  }

  let html = '';
  analysisTypes.forEach(function(a, idx) {
    html += `
      <div class="stats-item">
        <div class="stats-item-name">
          <div class="stats-item-avatar">${escapeHtml(a.code.substring(0, 2))}</div>
          <span>${escapeHtml(a.name)} <small class="text-muted">(${escapeHtml(a.code)})</small></span>
        </div>
        <div class="stats-item-counts">
          <span class="stats-count total" title="Total">${a.total}</span>
          <span class="stats-count approved" title="Approved">${a.approved}</span>
          <span class="stats-count pending" title="Pending">${a.pending}</span>
          ${a.rejected > 0 ? `<span class="stats-count rejected" title="Rejected">${a.rejected}</span>` : ''}
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}
