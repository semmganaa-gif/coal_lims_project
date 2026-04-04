/**
 * water_summary.js - Усны шинжилгээний нэгтгэл
 * AG Grid v29+ дэмжлэгтэй
 * Depends on: water_utils.js (WATER_UTILS global)
 */

/* ========================================
   WATER SUMMARY GRID MODULE
======================================== */

const WaterSummaryGrid = (function() {
  'use strict';

  // Shared utils from water_utils.js
  var U = window.WATER_UTILS || {};
  var formatValue = U.formatValue || function(c,v){ return v == null ? '' : String(v); };
  var formatLimit = U.formatLimit || function(l){ return ''; };
  var escapeHtml = U.escapeHtml || function(s){ return String(s || ''); };
  var isOverLimit = U.isOverLimit || function(){ return false; };
  var isWithinLimit = U.isWithinLimit || function(){ return false; };
  var isDetectFail = U.isDetectFail || function(){ return false; };
  var isDetectPass = U.isDetectPass || function(){ return false; };
  var WATER_CHEM_COLUMNS = U.WATER_CHEM_COLUMNS || [];

  // Config from HTML
  var CONFIG = (typeof WATER_SUMMARY_CONFIG !== 'undefined') ? WATER_SUMMARY_CONFIG : {};
  var URLS = CONFIG.urls || {};

  // Grid instance
  var gridApi = null;

  // Column state storage
  var COL_STATE_KEY = 'water_summary_col_state_v2';

  // Date filter state
  var dateFrom = null;
  var dateTo = null;

  // Data holders
  var chemParams = [];

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
      logger.warn('Auto size columns error:', e);
      // Fallback: sizeColumnsToFit
      try {
        gridApi.sizeColumnsToFit();
      } catch (e2) {
        logger.warn('Size columns to fit error:', e2);
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
      logger.warn('Failed to save column state:', e);
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
      logger.warn('Failed to restore column state:', e);
    }
  }

  /* -------- CELL RENDERERS -------- */

  function sampleNameRenderer(params) {
    if (!params.data) return '-';
    const name = escapeHtml(params.value || params.data.sample_name || '-');
    const code = escapeHtml(params.data.sample_code || '');
    return '<span class="ws-sample-link" title="' + code + '">' + name + '</span>';
  }

  /* -------- RETEST CELL RENDERERS -------- */

  /**
   * Химийн баганын cellRenderer — утга + давтах товч (hover дээр харагдана)
   */
  function chemResultRenderer(params) {
    if (params.value == null || params.value === '') return '';
    var field = params.colDef.field;
    var text = escapeHtml(formatValue(field, params.value));
    var rid = params.data && params.data._result_ids ? params.data._result_ids[field] : null;
    if (!rid) return text;
    return '<span class="ws-result-cell">'
      + '<span class="ws-result-value">' + text + '</span>'
      + '<button class="ws-retest-btn" data-rid="' + rid + '" title="Давтах">&#x21BB;</button>'
      + '</span>';
  }

  /* -------- RETEST HANDLER -------- */

  function handleRetestClick(resultId) {
    var msg = 'Энэ үр дүнг устгаж дахин шинжилгээ хийх үү?';
    if (!confirm(msg)) return;

    var url = (URLS.retest || '/labs/water-lab/chemistry/api/retest') + '/' + resultId;
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CONFIG.csrfToken || ''
      }
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.success) {
        refreshData();
      } else {
        alert('Алдаа: ' + (data.message || 'Тодорхойгүй'));
      }
    })
    .catch(function(err) {
      alert('Сүлжээний алдаа: ' + err.message);
    });
  }

  /* -------- BUILD COLUMN DEFINITIONS -------- */

  function buildColumnDefs(chemP) {
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
        cellRenderer: chemResultRenderer,
        cellClassRules: (function(limit) {
          return {
            'cell-over-limit': function(params) { return isOverLimit(limit, params.value); },
            'cell-within-limit': function(params) { return isWithinLimit(limit, params.value); },
            'cell-empty': function(params) { return params.value == null || params.value === ''; }
          };
        })(p.mns_limit)
      };
      chemChildren.push(colDef);
    }

    cols.push({
      headerName: 'Chemistry',
      headerClass: 'chem-header-group',
      marryChildren: false,
      children: chemChildren
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
        suppressHeaderMenuButton: true,
        suppressFloatingFilterButton: true
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
      onCellClicked: function(params) {
        // Давтах товч detect
        if (params.event && params.event.target) {
          var btn = params.event.target.closest('.ws-retest-btn');
          if (btn) {
            var rid = btn.getAttribute('data-rid');
            if (rid) handleRetestClick(rid);
          }
        }
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
    var url = URLS.summaryData || '/labs/water/api/summary_data';
    var params = [];
    if (dateFrom) params.push('date_from=' + encodeURIComponent(dateFrom));
    if (dateTo) params.push('date_to=' + encodeURIComponent(dateTo));
    if (params.length) url += '?' + params.join('&');

    fetch(url)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        chemParams = data.chem_params || [];
        // MNS limit-ийг серверээс merge хийх
        if (U.mergeMnsLimits) U.mergeMnsLimits(chemParams);
        if (callback) callback(null, data);
      })
      .catch(function(err) {
        logger.error('Load data error:', err);
        if (callback) callback(err, null);
      });
  }

  /* -------- RENDER GRID -------- */

  function renderGrid(rows) {
    const gridDiv = document.getElementById('waterSummaryGrid');
    if (!gridDiv) {
      logger.error('Grid container #waterSummaryGrid not found');
      return;
    }

    // Update row count
    const rowCountEl = document.getElementById('rowCount');
    if (rowCountEl) rowCountEl.textContent = rows.length;

    const columnDefs = buildColumnDefs(chemParams);

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
      logger.error('Grid creation error:', e);
      gridDiv.textContent = 'Хүснэгт үүсгэхэд алдаа: ' + e.message;
      gridDiv.style.cssText = 'padding:40px;text-align:center;color:#dc3545;';
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
      alert('Хүснэгт ачаалагдаагүй байна.');
      return;
    }

    const today = new Date().toISOString().slice(0, 10);
    gridApi.exportDataAsCsv({
      fileName: 'water_summary_' + today + '.csv',
      processCellCallback: function(params) {
        // cellRenderer HTML-г export-д оруулахгүй, зөвхөн raw value
        var v = params.value;
        return v != null ? v : '';
      },
      processHeaderCallback: function(params) {
        return (params.column.getColDef().headerName || '').replace(/\n/g, ' ');
      }
    });
  }

  function copySelected() {
    if (!gridApi) {
      alert('Хүснэгт ачаалагдаагүй байна.');
      return;
    }

    const nodes = gridApi.getSelectedNodes();
    if (nodes.length === 0) {
      alert('Хуулах мөрүүдээ сонгоно уу.');
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
        .then(function() { alert(nodes.length + ' мөр хуулагдлаа!'); })
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
      alert(count + ' мөр хуулагдлаа!');
    } catch (e) {
      alert('Хуулахад алдаа гарлаа.');
    }
    document.body.removeChild(ta);
  }

  /* -------- PUBLIC API -------- */

  /** Огноог YYYY-MM-DD string болгох */
  function toDateStr(d) {
    var mm = String(d.getMonth() + 1).padStart(2, '0');
    var dd = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + mm + '-' + dd;
  }

  /** Preset товчнуудын active toggle */
  function setActivePreset(days) {
    var btns = document.querySelectorAll('.ws-date-preset');
    for (var i = 0; i < btns.length; i++) {
      btns[i].classList.toggle('active', Number(btns[i].dataset.days) === days);
    }
  }

  /** Огнооны filter-г тохируулж data дахин ачаалах */
  function applyDatePreset(days) {
    var elFrom = document.getElementById('dateFrom');
    var elTo = document.getElementById('dateTo');
    if (days > 0) {
      var now = new Date();
      dateTo = toDateStr(now);
      var from = new Date(now);
      from.setDate(from.getDate() - days);
      dateFrom = toDateStr(from);
    } else {
      dateFrom = null;
      dateTo = null;
    }
    if (elFrom) elFrom.value = dateFrom || '';
    if (elTo) elTo.value = dateTo || '';
    setActivePreset(days);
    refreshData();
  }

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
          alert('Архивлах дээжүүдээ сонгоно уу.');
          return;
        }
        if (!confirm('Сонгосон ' + ids.length + ' дээжийг архивлахдаа итгэлтэй байна уу?')) {
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
        alert('Тайлангийн дээжүүдээ сонгоно уу.');
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
          alert('Тайлан амжилттай үүслээ: ' + data.report_number);
          window.location.href = data.redirect_url;
        } else {
          alert('Алдаа: ' + (data.error || 'Тодорхойгүй'));
        }
      })
      .catch(err => {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
        alert('Сүлжээний алдаа: ' + err.message);
      });
    }

    // Water chemistry report button
    const btnReportWater = document.getElementById('btnReportWater');
    if (btnReportWater) {
      btnReportWater.addEventListener('click', function() {
        createReport('water_chemistry', this, '<i class="bi bi-file-earmark-pdf me-1"></i>Chemistry');
      });
    }

    // ── Date filter ──
    var elDateFrom = document.getElementById('dateFrom');
    var elDateTo = document.getElementById('dateTo');

    // Preset товчнууд
    var presetBtns = document.querySelectorAll('.ws-date-preset');
    for (var pi = 0; pi < presetBtns.length; pi++) {
      presetBtns[pi].addEventListener('click', function() {
        applyDatePreset(Number(this.dataset.days));
      });
    }

    // Гар огноо сонголт
    if (elDateFrom) {
      elDateFrom.addEventListener('change', function() {
        dateFrom = this.value || null;
        setActivePreset(-1); // clear preset highlight
        refreshData();
      });
    }
    if (elDateTo) {
      elDateTo.addEventListener('change', function() {
        dateTo = this.value || null;
        setActivePreset(-1);
        refreshData();
      });
    }

    // Initial load — default 7 хоног
    applyDatePreset(7);
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
    logger.error('WaterSummaryGrid init error:', e);
  }
});
