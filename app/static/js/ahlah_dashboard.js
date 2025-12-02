/* ===============================
 * 1) DoD,D?D,-?.O_??D???D3?, renderer (raw_data) - D`OrD?D-D? D?D?D'D~D>D`D?D?
 * =============================== */
const DEFAULT_PARALLEL_SCHEMA = {
  title: "Parallels snapshot",
  columns: [
    { key: "num", label: "?" },
    { key: "m1", label: "m1", format: "float", precision: 4 },
    { key: "m2", label: "m2", format: "float", precision: 4 },
    { key: "m3", label: "m3", format: "float", precision: 4 },
    { key: "result", label: "Result", format: "float", precision: 3 }
  ]
};

const SUMMARY_FIELDS = [
  { key: "avg", label: "Average", format: "float", precision: 3 },
  { key: "diff", label: "Diff / T", format: "float", precision: 3 },
  { key: "result", label: "Result", format: "float", precision: 3 },
  { key: "final_result", label: "Final Result", format: "float", precision: 3 },
  { key: "A", label: "A (pan + sample)", format: "float", precision: 3 },
  { key: "B", label: "B (pan only)", format: "float", precision: 3 },
  { key: "C", label: "C (residue)", format: "float", precision: 3 },
  { key: "weight", label: "Weight", format: "float", precision: 3 },
  { key: "limit_used", label: "Limit used", format: "float", precision: 3 },
  { key: "limit_mode", label: "Limit mode" },
  { key: "t_exceeded", label: "T exceeded", format: "boolean" },
  { key: "retest_mode", label: "Retest mode" },
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
    return value;
  }
  if (format === "boolean") {
    return value ? "Yes" : "No";
  }
  return escapeHtml(value);
}

function deriveParallels(raw) {
  if (raw && Array.isArray(raw.parallels) && raw.parallels.length) {
    return raw.parallels;
  }
  const rows = [];
  ["p1", "p2", "p3"].forEach((key) => {
    const val = raw && raw[key];
    if (val && typeof val === "object" && Object.keys(val).length) {
      rows.push({ label: key, ...val });
    }
  });
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
      return `<th>${label}${unit}</th>`;
    })
    .join("");
  const body = parallels
    .map((row) => {
      const cells = columns
        .map((col) => `<td>${formatValue(row && row[col.key], col)}</td>`)
        .join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");
  return `
    <div class="table-responsive mb-1">
      <table class="table table-sm table-bordered align-middle text-center mb-0">
        <thead class="table-light"><tr>${header}</tr></thead>
        <tbody>${body}</tbody>
      </table>
    </div>`;
}

function buildSummarySection(raw, rowCtx) {
  if (!raw || typeof raw !== "object") raw = {};
  const segments = [];
  const seen = new Set();

  function append(label, value, cfg) {
    if (value === undefined || value === null || value === "") return;
    const key = `${label}-${cfg?.key || label}`;
    if (seen.has(key)) return;
    seen.add(key);
    segments.push(
      `<div class="d-flex justify-content-between">
        <span class="text-muted">${escapeHtml(label)}</span>
        <span class="fw-semibold">${formatValue(value, cfg)}</span>
      </div>`
    );
  }

  SUMMARY_FIELDS.forEach((cfg) => {
    append(cfg.label, raw[cfg.key], cfg);
  });

  const fallbackFields = [
    { key: "final_value", label: "Final Value", format: "float", precision: 3 },
    { key: "t_value", label: "Diff / T", format: "float", precision: 3 },
    { key: "status", label: "Status" },
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

function ReviewDataRenderer(params) {
  const raw = params.data.raw_data || {};
  const rowCtx = params.data || {};
  const code = rowCtx.analysis_code || "";
  const schema = getParallelSchema(code);
  const parallels = deriveParallels(raw);
  const summaryBlock = buildSummarySection(raw, rowCtx);
  const hasSummary = Boolean(summaryBlock);

  let html = '<div class="review-data-cell" style="font-size:0.85em;">';

  const hasRaw = raw && Object.keys(raw).length;
  const showRawFallback = !parallels.length && hasRaw && !hasSummary;

  if (parallels.length) {
    html += `<div class="text-muted small fw-semibold mb-1">${escapeHtml(schema.title)}</div>`;
    html += renderParallelTable(parallels, schema);
  } else if (showRawFallback) {
    html += `<pre class="raw-json-box small mb-0" style="white-space:pre-wrap;">${escapeHtml(JSON.stringify(raw, null, 2))}</pre>`;
  } else {
    html += '<span class="text-muted small">Raw data not available</span>';
  }

  if (hasSummary && !parallels.length) {
    html += summaryBlock;
  }

  if (!showRawFallback) {
    html += buildRawJsonSection(raw);
  }
  html += "</div>";
  return html;
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
      "Сүүлд шинэчилсэн: " +
      now.toLocaleString("mn-MN", { hour12: false });
  }
}
/* ===============================
 * 2) Actions renderer (approve / reject)
 * =============================== */
function ActionsRenderer(params) {
  const resultId = params.data.result_id;
  const sampleCode = params.data.sample_code;
  const analysisName = params.data.analysis_name;

  const approveBtn = `
    <button type="button" class="btn btn-success btn-sm w-100 mb-1 btn-approve" data-id="${resultId}">
      <i class="bi bi-check-circle"></i> Зөвшөөрөх
    </button>
  `;

  const rejectBtn = `
    <button type="button" class="btn btn-outline-danger btn-sm w-100 btn-open-reject-modal"
      data-bs-toggle="modal" data-bs-target="#rejectModal"
      data-result-id="${resultId}" data-sample-code="${sampleCode}" data-analysis-name="${analysisName}">
      <i class="bi bi-x-circle"></i> Буцаах
    </button>
  `;
  return `<div class="d-flex flex-column gap-1 p-1">${approveBtn}${rejectBtn}</div>`;
}

/* ===============================
 * 3) AG Grid options
 * =============================== */
const gridOptions = {
  columnDefs: [
    {
      headerName: "Дээж / Шинжилгээ",
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
                      <i class="bi bi-arrow-repeat"></i> 3:3 дахин хийх
                    </span></div>`;
        } else if (status === 'rejected') {
           // window.ERROR_LABELS нь дээд талд тодорхойлогдсон map
           const reasonText = window.ERROR_LABELS[errorReason] || errorReason || 'Буцаасан';
           badge = `<div class="mt-1"><span class="badge bg-danger text-wrap text-start" style="line-height:1.3; font-weight:normal;">
                      <i class="bi bi-exclamation-triangle-fill"></i> ${reasonText}
                    </span></div>`;
        } else if (status === 'pending_review') {
           badge = '<span class="badge bg-warning text-dark ms-1">Хүлээгдэж буй</span>';
        }

        return `<div class="d-flex flex-column py-1">
                  <span class="fw-bold text-primary" style="font-size:0.95rem;">${p.sample_code}</span>
                  <small class="text-muted fw-semibold">${p.analysis_name}</small>
                  ${badge}
                </div>`;
      },
      filter: true,
      floatingFilter: true,
      minWidth: 260,
      autoHeight: true
    },
    {
      headerName: "Тооцооны өгөгдөл (Raw Data)",
      cellRenderer: ReviewDataRenderer,
      autoHeight: true,
      minWidth: 450,
      flex: 2
    },
    {
      headerName: "T",
      field: "t_value",
      width: 80,
      cellStyle: {textAlign: 'center', fontWeight: 'bold', verticalAlign: 'middle'},
      valueFormatter: p => (p.value != null) ? Number(p.value).toFixed(3) : '-'
    },
    {
      headerName: "Эцсийн дүн",
      field: "final_value",
      width: 120,
      cellStyle: {textAlign: 'right', fontWeight: 'bold', color: '#198754', verticalAlign: 'middle', fontSize:'1.1em'},
      valueFormatter: p => (p.value != null) ? Number(p.value).toFixed(3) : '-'
    },
    {
      headerName: "Хийсэн / Огноо",
      cellRenderer: p => `
        <div class="small lh-sm py-1">
          <div class="fw-bold"><i class="bi bi-person-circle"></i> ${p.data.user_name}</div>
          <div class="text-muted" style="font-size:0.75rem;">${p.data.updated_at}</div>
        </div>`,
      width: 170,
      cellStyle: {verticalAlign: 'middle'}
    },
    {
      headerName: "Үйлдэл",
      cellRenderer: ActionsRenderer,
      width: 140,
      pinned: 'right',
      cellStyle: {display: 'flex', alignItems: 'center', justifyContent: 'center'}
    }
  ],
  rowData: [],
  rowHeight: null,
  suppressRowTransform: true,
  defaultColDef: {
    resizable: true,
    sortable: true,
    filter: true,
    suppressHeaderMenuButton: true
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
      console.error('Error:', error);
      gridDiv.innerHTML = '<div class="alert alert-danger m-3">Өгөгдөл ачаалахад алдаа гарлаа.</div>';
    });

  // Approve Button Listener
  document.addEventListener('click', function(e) {
    if (e.target.closest('.btn-approve')) {
        const btn = e.target.closest('.btn-approve');
        const id = btn.dataset.id;
        if(!confirm("Энэ үр дүнг баталгаажуулах уу?")) return;

        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/api/update_result_status/${id}/approved`;
        document.body.appendChild(form);
        form.submit();
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
    alert('Буцаах ангилал сонгоно уу.');
    return;
  }

  const $btn = $(this).find('button[type="submit"]');
  $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> Уншиж байна...');

  $.ajax({
    url: '/api/update_result_status/' + id + '/rejected',
    method: 'POST',
    contentType: 'application/json',
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
      console.error('❌ KPI summary load failed:', err);
    });
}

// Аль хэдийн өөр DOMContentLoaded listener байж болно – давхар байхад асуудалгүй.
document.addEventListener('DOMContentLoaded', function () {
  loadAhlahKpiSummary();
});
