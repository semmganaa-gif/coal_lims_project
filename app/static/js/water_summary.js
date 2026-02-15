/**
 * water_summary.js - Усны шинжилгээний нэгтгэл
 * AG Grid v29+ дэмжлэгтэй
 */

/* ========================================
   WATER SUMMARY GRID MODULE
======================================== */

const WaterSummaryGrid = (function() {
  'use strict';

  // Config from HTML
  const CONFIG = (typeof WATER_SUMMARY_CONFIG !== 'undefined') ? WATER_SUMMARY_CONFIG : {};
  const URLS = CONFIG.urls || {};

  // Grid instance
  let gridApi = null;

  // Column state storage
  const COL_STATE_KEY = 'water_summary_col_state_v2';

  // Data holders
  let chemParams = [];
  let microFields = [];

  /* -------- UTILITY FUNCTIONS -------- */

  function safeNumber(val) {
    if (val === null || val === undefined || val === '' || val === 'null') return null;
    const str = String(val).replace(',', '').trim();
    const num = parseFloat(str);
    return isNaN(num) ? null : num;
  }

  function formatValue(code, val) {
    if (val == null || val === '') return '';
    const n = parseFloat(val);
    if (isNaN(n)) return String(val);
    if (Math.abs(n) < 0.01 && n !== 0) return n.toExponential(2);
    if (n === Math.floor(n)) return n.toString();
    return n.toFixed(n < 1 ? 3 : 2);
  }

  function formatLimit(limit) {
    if (!limit) return '';
    if (Array.isArray(limit)) {
      const lo = limit[0], hi = limit[1];
      if (lo !== null && hi !== null) return lo + '—' + hi;
      if (hi !== null) return '\u2264' + hi;
      if (lo !== null) return '\u2265' + lo;
    }
    return String(limit);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* -------- LIMIT CHECK FUNCTIONS -------- */

  function isOverLimit(limit, value) {
    if (!limit || value == null) return false;
    const n = parseFloat(value);
    if (isNaN(n)) return false;
    if (Array.isArray(limit)) {
      const lo = limit[0], hi = limit[1];
      return (lo !== null && n < lo) || (hi !== null && n > hi);
    }
    return false;
  }

  function isWithinLimit(limit, value) {
    if (!limit || value == null) return false;
    const n = parseFloat(value);
    if (isNaN(n)) return false;
    if (Array.isArray(limit)) {
      const lo = limit[0], hi = limit[1];
      return !((lo !== null && n < lo) || (hi !== null && n > hi));
    }
    return false;
  }

  function isDetectFail(value) {
    if (value == null || value === '') return false;
    const s = String(value).trim().toLowerCase();
    if (['илрэсэн', 'илэрсэн', 'detected', '+'].includes(s)) return true;
    const n = parseFloat(value);
    return !isNaN(n) && n > 0;
  }

  function isDetectPass(value) {
    if (value == null || value === '') return false;
    const s = String(value).trim().toLowerCase();
    if (['илрээгүй', 'not detected', '-', '0'].includes(s)) return true;
    const n = parseFloat(value);
    return !isNaN(n) && n === 0;
  }

  /* -------- AUTO SIZE COLUMNS -------- */

  function autoSizeColumns() {
    if (!gridApi) return;
    try {
      // Бүх баганын ID-г авах
      var allColumnIds = [];
      var columns = gridApi.getColumns ? gridApi.getColumns() : [];
      if (columns && columns.length > 0) {
        for (var i = 0; i < columns.length; i++) {
          allColumnIds.push(columns[i].getColId());
        }
        // Баганын өргөнийг контентоор тохируулах
        gridApi.autoSizeColumns(allColumnIds, false);
      }
    } catch (e) {
      console.warn('Auto size columns error:', e);
      // Fallback: sizeColumnsToFit
      try {
        gridApi.sizeColumnsToFit();
      } catch (e2) {
        console.warn('Size columns to fit error:', e2);
      }
    }
  }

  /* -------- COLUMN STATE -------- */

  function saveColumnState() {
    if (!gridApi) return;
    try {
      const state = gridApi.getColumnState();
      localStorage.setItem(COL_STATE_KEY, JSON.stringify(state));
    } catch (e) {
      console.warn('Failed to save column state:', e);
    }
  }

  function restoreColumnState() {
    if (!gridApi) return;
    try {
      const saved = localStorage.getItem(COL_STATE_KEY);
      if (saved) {
        const state = JSON.parse(saved);
        gridApi.applyColumnState({ state: state, applyOrder: true });
      }
    } catch (e) {
      console.warn('Failed to restore column state:', e);
    }
  }

  /* -------- CELL RENDERERS -------- */

  function sampleNameRenderer(params) {
    if (!params.data) return '-';
    const name = escapeHtml(params.value || params.data.sample_name || '-');
    const code = escapeHtml(params.data.sample_code || '');
    return `<span class="ws-sample-link" title="${code}">${name}</span>`;
  }

  /* -------- FIXED COLUMN ORDER & MNS LIMITS -------- */

  // Усны химийн баганууд - олон улсын нэршил, богино код
  // Унд ахуйн + Бохир усны параметрүүд нэгтгэсэн
  // primary: true = үргэлж харагдана, false = зөвхөн group дэлгэсэн үед
  const WATER_CHEM_COLUMNS = [
    // Унд ахуйн ус - үндсэн 5 багана үргэлж харагдана
    { code: 'COLOR', name: 'Color', shortName: 'Color', unit: '°', mns_limit: [null, 20], primary: true },
    { code: 'EC', name: 'Electrical Conductivity', shortName: 'EC', unit: 'µS/cm', mns_limit: [null, 1000], primary: true },
    { code: 'PH', name: 'pH', shortName: 'pH', unit: '', mns_limit: [6.5, 8.5], primary: true },
    { code: 'F_W', name: 'Fluoride', shortName: 'F⁻', unit: 'mg/L', mns_limit: [0.7, 1.5], primary: true },
    { code: 'CL_FREE', name: 'Free Chlorine', shortName: 'Cl₂', unit: 'mg/L', mns_limit: [0.2, 0.3], primary: true },
    // Дэлгэсэн үед харагдах баганууд
    { code: 'HARD', name: 'Total Hardness', shortName: 'Hard', unit: 'meq/L', mns_limit: [null, 7] },
    { code: 'NH4', name: 'Ammonium Ion', shortName: 'NH₄⁺', unit: 'mg/L', mns_limit: [null, 1.5] },
    { code: 'NO2', name: 'Nitrite Ion', shortName: 'NO₂⁻', unit: 'mg/L', mns_limit: [null, 1] },
    { code: 'FE_W', name: 'Iron', shortName: 'Fe', unit: 'mg/L', mns_limit: [null, 0.3] },
    // Бохир ус (давхардаагүй)
    { code: 'TDS', name: 'Total Dissolved Solids', shortName: 'TDS', unit: 'mg/L', mns_limit: [null, 400] },
    { code: 'CL_W', name: 'Chloride', shortName: 'Cl⁻', unit: 'mg/L', mns_limit: [null, 350] },
    { code: 'PO4', name: 'Phosphate Ion', shortName: 'PO₄³⁻', unit: 'mg/L', mns_limit: [null, 5] },
    { code: 'BOD', name: 'Biochemical Oxygen Demand', shortName: 'BOD', unit: 'mg/L', mns_limit: [null, 20] },
    // Лагийн шинжилгээ
    { code: 'SLUDGE_VOL', name: 'Sludge Volume', shortName: 'SV', unit: 'mL', mns_limit: [70, 80] },
    { code: 'SLUDGE_DOSE', name: 'Sludge Dose', shortName: 'SD', unit: 'g/L', mns_limit: [2, 4] },
    { code: 'SLUDGE_INDEX', name: 'Sludge Index', shortName: 'SI', unit: 'mL/g', mns_limit: [80, 150] }
  ];

  // Микробиологийн баганууд - Ус, Агаар, Арчдас нэгтгэсэн
  const MICRO_COLUMNS = [
    // CFU (ус: 22°C, 37°C)
    { code: 'cfu_22', headerName: 'CFU 22°C', headerTooltip: 'MNS ISO 6222:1998 / per 1 mL ≤100', mns_limit: [null, 100], integer: true },
    { code: 'cfu_37', headerName: 'CFU 37°C', headerTooltip: 'MNS ISO 6222:1998 / per 1 mL ≤100', mns_limit: [null, 100], integer: true },
    // CFU Дундаж (ус + арчдас нэгтгэсэн)
    { code: 'cfu_avg', headerName: 'CFU Avg', headerTooltip: 'Water: MNS ISO 6222 ≤100 / Swab: MNS 6410 <100', mns_limit: [null, 100], integer: true },
    // E.coli (ус + арчдас)
    { code: 'ecoli', headerName: 'E.coli', headerTooltip: 'Water: MNS ISO 9308-1 / Swab: MNS 6410:2018', detect: true, italic: true },
    // Salmonella (ус + арчдас)
    { code: 'salmonella', headerName: 'Salmonella', headerTooltip: 'Water: MNS ISO 19250 / Swab: MNS 6410:2018', detect: true, italic: true },
    // S.aureus (агаар + арчдас)
    { code: 'staph', headerName: 'S.aureus', headerTooltip: 'Air: MNS 5484 / Swab: MNS 6410:2018', detect: true, italic: true },
    // Агаарын бактерийн тоо
    { code: 'air_cfu', headerName: 'Bacteria Count', headerTooltip: 'MNS 5484:2005 / per 1m³ <3000', mns_limit: [null, 3000], integer: true }
  ];

  /* -------- BUILD COLUMN DEFINITIONS -------- */

  function buildColumnDefs(chemP, microF) {
    const cols = [];

    // Selection checkbox
    cols.push({
      headerName: '',
      field: '_sel',
      checkboxSelection: true,
      headerCheckboxSelection: true,
      headerCheckboxSelectionFilteredOnly: true,
      width: 40, minWidth: 40, maxWidth: 40,
      pinned: 'left',
      sortable: false,
      filter: false,
      resizable: false,
      suppressMovable: true,
      lockPosition: 'left'
    });

    // Бүртгэсэн огноо
    cols.push({
      headerName: 'Registered',
      field: 'received_date',
      width: 95,
      minWidth: 85,
      pinned: 'left',
      sortable: true,
      filter: 'agTextColumnFilter',
      floatingFilter: true,
      cellStyle: { fontWeight: '600', color: '#1e40af' }
    });

    // Хими лаб номер
    cols.push({
      headerName: 'Chem #',
      field: 'chem_lab_id',
      width: 90,
      minWidth: 90,
      maxWidth: 90,
      pinned: 'left',
      sortable: false,
      filter: 'agTextColumnFilter',
      floatingFilter: true,
      resizable: false,
      cellStyle: { textAlign: 'center', fontWeight: '600', color: '#3b82f6' }
    });

    // Микро лаб номер
    cols.push({
      headerName: 'Micro #',
      field: 'micro_lab_id',
      width: 95,
      minWidth: 95,
      maxWidth: 95,
      pinned: 'left',
      sortable: false,
      filter: 'agTextColumnFilter',
      floatingFilter: true,
      resizable: false,
      cellStyle: { textAlign: 'center', fontWeight: '600', color: '#10b981' }
    });

    // Сорьцын нэр
    cols.push({
      headerName: 'Sample Name',
      field: 'sample_name',
      width: 340,
      minWidth: 280,
      pinned: 'left',
      sortable: true,
      filter: 'agTextColumnFilter',
      floatingFilter: true,
      cellRenderer: sampleNameRenderer,
      tooltipValueGetter: function(p) {
        return p.data ? p.data.sample_code : '';
      }
    });

    // Химийн баганууд - олон улсын нэршил
    var chemChildren = [];
    for (var i = 0; i < WATER_CHEM_COLUMNS.length; i++) {
      var p = WATER_CHEM_COLUMNS[i];
      var colDef = {
        headerName: p.shortName,
        headerTooltip: p.name + (p.unit ? ' (' + p.unit + ')' : '') + ' — MNS: ' + (formatLimit(p.mns_limit) || '-'),
        field: p.code,
        minWidth: 42,
        maxWidth: 70,
        sortable: false,
        filter: false,
        floatingFilter: false,
        type: 'numericColumn',
        headerClass: 'chem-header',
        valueFormatter: (function(code) {
          return function(params) { return formatValue(code, params.value); };
        })(p.code),
        cellClassRules: (function(limit) {
          return {
            'cell-over-limit': function(params) { return isOverLimit(limit, params.value); },
            'cell-within-limit': function(params) { return isWithinLimit(limit, params.value); },
            'cell-empty': function(params) { return params.value == null || params.value === ''; }
          };
        })(p.mns_limit)
      };
      // primary биш баганууд зөвхөн group дэлгэсэн үед харагдана
      if (!p.primary) {
        colDef.columnGroupShow = 'open';
      }
      chemChildren.push(colDef);
    }

    cols.push({
      headerName: 'Chemistry ▸',
      headerClass: 'chem-header-group',
      marryChildren: false,
      children: chemChildren
    });

    // Микробиологийн баганууд (5 багана)
    var microChildren = [];

    for (var m = 0; m < MICRO_COLUMNS.length; m++) {
      var mc = MICRO_COLUMNS[m];
      var isDetect = !!mc.detect;
      var headerClass = 'micro-header';
      if (mc.italic) headerClass += ' micro-italic-header';

      microChildren.push({
        headerName: mc.headerName,
        headerTooltip: mc.headerTooltip,
        field: mc.code,
        minWidth: mc.minWidth || 70,
        maxWidth: mc.maxWidth || 120,
        sortable: false,
        filter: false,
        floatingFilter: false,
        headerClass: headerClass,
        valueFormatter: isDetect ? function(params) {
          if (params.value == null || params.value === '') return '';
          var s = String(params.value).trim().toLowerCase();
          if (s === '0' || s === 'илрээгүй' || s === 'not detected' || s === '-') return 'Not Detected';
          if (!isNaN(parseFloat(params.value)) && parseFloat(params.value) > 0) return 'Detected';
          return params.value;
        } : (function(isInt) {
          return function(params) {
            if (params.value == null || params.value === '') return '';
            // Таслал/цэгийг боловсруулах
            var val = String(params.value).replace(',', '.');
            var n = parseFloat(val);
            if (isNaN(n)) return params.value;
            return isInt ? Math.round(n).toString() : formatValue('', n);
          };
        })(mc.integer),
        cellClassRules: isDetect ? {
          'cell-detect-fail': function(params) { return isDetectFail(params.value); },
          'cell-detect-pass': function(params) { return isDetectPass(params.value); },
          'cell-empty': function(params) { return params.value == null || params.value === ''; }
        } : (function(limit) {
          return {
            'cell-over-limit': function(params) { return isOverLimit(limit, params.value); },
            'cell-within-limit': function(params) { return isWithinLimit(limit, params.value); },
            'cell-empty': function(params) { return params.value == null || params.value === ''; }
          };
        })(mc.mns_limit)
      });
    }

    cols.push({
      headerName: 'Microbiology',
      headerTooltip: 'MNS 0900:2018',
      headerClass: 'micro-header-group',
      marryChildren: false,
      children: microChildren
    });

    return cols;
  }

  /* -------- GRID OPTIONS -------- */

  function createGridOptions(columnDefs, rowData) {
    return {
      columnDefs: columnDefs,
      rowData: rowData,
      defaultColDef: {
        resizable: true,
        sortable: true,
        filter: true,
        suppressMenu: true
      },
      rowHeight: 28,
      headerHeight: 32,
      groupHeaderHeight: 32,
      floatingFiltersHeight: 28,
      rowSelection: 'multiple',
      suppressCellFocus: true,
      enableBrowserTooltips: true,
      tooltipShowDelay: 200,
      getRowId: function(params) {
        return String(params.data.sample_id || params.data.id);
      },
      onGridReady: function(params) {
        gridApi = params.api;
        setTimeout(restoreColumnState, 100);
      },
      onFirstDataRendered: function(params) {
        // Баганын өргөнийг контентоор автомат тохируулах
        autoSizeColumns();
      },
      onColumnMoved: saveColumnState,
      onColumnPinned: saveColumnState,
      onColumnVisible: function(params) {
        saveColumnState();
        // Column харагдах үед auto-size
        setTimeout(autoSizeColumns, 50);
      },
      onColumnResized: function(params) {
        if (params.finished) saveColumnState();
      }
    };
  }

  /* -------- DATA LOADING -------- */

  function loadData(callback) {
    const url = URLS.summaryData || '/labs/water/api/summary_data';

    fetch(url)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        chemParams = data.chem_params || [];
        microFields = data.micro_fields || [];
        if (callback) callback(null, data);
      })
      .catch(function(err) {
        console.error('Load data error:', err);
        if (callback) callback(err, null);
      });
  }

  /* -------- RENDER GRID -------- */

  function renderGrid(rows) {
    const gridDiv = document.getElementById('waterSummaryGrid');
    if (!gridDiv) {
      console.error('Grid container #waterSummaryGrid not found');
      return;
    }

    // Update row count
    const rowCountEl = document.getElementById('rowCount');
    if (rowCountEl) rowCountEl.textContent = rows.length;

    const columnDefs = buildColumnDefs(chemParams, microFields);

    // Update stats
    updateStats();

    if (gridApi) {
      // Update existing grid
      gridApi.setGridOption('columnDefs', columnDefs);
      gridApi.setGridOption('rowData', rows);
      return;
    }

    // Check AG Grid
    if (typeof agGrid === 'undefined') {
      gridDiv.innerHTML = '<div style="padding:40px;text-align:center;color:#dc3545;">AG Grid library not loaded.</div>';
      return;
    }

    // Create new grid
    const gridOptions = createGridOptions(columnDefs, rows);

    try {
      if (typeof agGrid.createGrid === 'function') {
        gridApi = agGrid.createGrid(gridDiv, gridOptions);
      } else if (typeof agGrid.Grid === 'function') {
        new agGrid.Grid(gridDiv, gridOptions);
        gridApi = gridOptions.api;
      }
    } catch (e) {
      console.error('Grid creation error:', e);
      gridDiv.innerHTML = '<div style="padding:40px;text-align:center;color:#dc3545;">Grid creation error: ' + e.message + '</div>';
    }
  }

  /* -------- UPDATE STATS -------- */

  function updateStats() {
    // Тогтсон баганууд: Хими 9, Микро 4
    // Статистик HTML дээр хатуу кодлогдсон
  }

  /* -------- EXPORT FUNCTIONS -------- */

  function exportCsv() {
    if (!gridApi) {
      alert('Grid not initialized.');
      return;
    }

    const today = new Date().toISOString().slice(0, 10);
    gridApi.exportDataAsCsv({
      fileName: 'water_summary_' + today + '.csv',
      processCellCallback: function(params) {
        return params.value != null ? params.value : '';
      },
      processHeaderCallback: function(params) {
        return (params.column.getColDef().headerName || '').replace(/\n/g, ' ');
      }
    });
  }

  function copySelected() {
    if (!gridApi) {
      alert('Grid not initialized.');
      return;
    }

    const nodes = gridApi.getSelectedNodes();
    if (nodes.length === 0) {
      alert('Please select rows to copy.');
      return;
    }

    // Get columns excluding selection and row number
    const columns = gridApi.getAllDisplayedColumns().filter(function(c) {
      const id = c.getColId();
      return id !== '_sel' && id !== '_seq';
    });

    // Header row
    const header = columns.map(function(c) {
      return (c.getColDef().headerName || '').replace(/\n/g, ' ');
    }).join('\t');

    // Data rows
    const dataRows = nodes.map(function(n) {
      return columns.map(function(c) {
        const v = n.data[c.getColId()];
        return v != null ? v : '';
      }).join('\t');
    }).join('\n');

    const text = header + '\n' + dataRows;

    // Copy to clipboard
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text)
        .then(function() { alert(nodes.length + ' rows copied!'); })
        .catch(function() { fallbackCopy(text, nodes.length); });
    } else {
      fallbackCopy(text, nodes.length);
    }
  }

  function fallbackCopy(text, count) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      alert(count + ' rows copied!');
    } catch (e) {
      alert('Error copying to clipboard.');
    }
    document.body.removeChild(ta);
  }

  /* -------- PUBLIC API -------- */

  function init() {
    const btnExportCsv = document.getElementById('btnExportCsv');
    const btnCopy = document.getElementById('btnCopy');
    const btnRefresh = document.getElementById('btnRefresh');
    const btnArchive = document.getElementById('btnArchive');

    // Export CSV button
    if (btnExportCsv) {
      btnExportCsv.addEventListener('click', exportCsv);
    }

    // Copy button
    if (btnCopy) {
      btnCopy.addEventListener('click', copySelected);
    }

    // Refresh button
    if (btnRefresh) {
      btnRefresh.addEventListener('click', function() {
        refreshData();
      });
    }

    // Archive button
    if (btnArchive) {
      btnArchive.addEventListener('click', function() {
        const ids = getSelectedIds();
        if (ids.length === 0) {
          alert('Please select samples to archive.');
          return;
        }
        if (!confirm('Are you sure you want to archive ' + ids.length + ' selected samples?')) {
          return;
        }
        const form = document.getElementById('archiveForm');
        const idsInput = document.getElementById('archiveSampleIds');
        if (form && idsInput) {
          idsInput.value = ids.join(',');
          form.submit();
        }
      });
    }

    // Report buttons helper function
    function createReport(labType, btn, originalHtml) {
      const ids = getSelectedIds();
      if (ids.length === 0) {
        alert('Please select samples to generate report.');
        return;
      }

      // Get date range from selected rows
      const nodes = gridApi.getSelectedNodes();
      let dateFrom = null, dateTo = null;
      nodes.forEach(n => {
        const d = n.data.received_date || n.data.sample_date;
        if (d) {
          if (!dateFrom || d < dateFrom) dateFrom = d;
          if (!dateTo || d > dateTo) dateTo = d;
        }
      });

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>...';

      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
      fetch('/pdf-reports/api/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          lab_type: labType,
          sample_ids: ids,
          date_from: dateFrom,
          date_to: dateTo
        })
      })
      .then(r => r.json())
      .then(data => {
        btn.disabled = false;
        btn.innerHTML = originalHtml;

        if (data.success) {
          alert('Report created successfully: ' + data.report_number);
          window.location.href = data.redirect_url;
        } else {
          alert('Error: ' + (data.error || 'Unknown'));
        }
      })
      .catch(err => {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
        alert('Network error: ' + err.message);
      });
    }

    // Water chemistry report button
    const btnReportWater = document.getElementById('btnReportWater');
    if (btnReportWater) {
      btnReportWater.addEventListener('click', function() {
        createReport('water', this, '<i class="bi bi-file-earmark-pdf me-1"></i>Chemistry');
      });
    }

    // Microbiology report button
    const btnReportMicro = document.getElementById('btnReportMicro');
    if (btnReportMicro) {
      btnReportMicro.addEventListener('click', function() {
        createReport('microbiology', this, '<i class="bi bi-file-earmark-pdf me-1"></i>Micro');
      });
    }

    // Initial load
    refreshData();
  }

  function refreshData() {
    const rowCountEl = document.getElementById('rowCount');
    if (rowCountEl) rowCountEl.textContent = '...';

    loadData(function(err, data) {
      if (err) {
        if (rowCountEl) rowCountEl.textContent = 'Алдаа';
        return;
      }
      renderGrid(data.rows || []);
    });
  }

  function getApi() {
    return gridApi;
  }

  function getSelectedIds() {
    if (!gridApi) return [];
    return gridApi.getSelectedNodes().map(function(n) {
      return n.data.sample_id || n.data.id;
    });
  }

  return {
    init: init,
    refreshData: refreshData,
    getApi: getApi,
    getSelectedIds: getSelectedIds,
    exportCsv: exportCsv,
    copySelected: copySelected
  };
})();


/* ========================================
   INITIALIZE ON DOM READY
======================================== */

document.addEventListener('DOMContentLoaded', function() {
  'use strict';

  try {
    WaterSummaryGrid.init();
  } catch (e) {
    console.error('WaterSummaryGrid init error:', e);
  }
});
