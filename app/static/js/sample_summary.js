/**
 * sample_summary.js - Найдвартай хувилбар
 * AG Grid v29+ дэмжлэгтэй
 */

/* ========================================
   1. CALENDAR LOGIC
   ✅ REFACTORED: Нийтлэг CalendarModule ашиглаж байна (calendar-module.js)
======================================== */

// Sample Summary-д зориулсан Calendar initialization
const SampleSummaryCalendar = (function() {
  'use strict';

  function init() {
    // CalendarModule байгаа эсэх шалгах
    if (typeof CalendarModule === 'undefined') {
      logger.warn('SampleSummaryCalendar: CalendarModule not loaded');
      return;
    }

    const startHidden = document.getElementById('start_date_hidden');
    const endHidden = document.getElementById('end_date_hidden');

    if (!startHidden || !endHidden) {
      logger.log('Calendar: Hidden inputs not found, skipping init');
      return;
    }

    let startCenter = CalendarModule.parseDate(startHidden.value);
    let endCenter = CalendarModule.parseDate(endHidden.value);

    const renderStart = function() {
      CalendarModule.buildCalendar('startCalendar', 'startCalLabel', startCenter, startHidden.value, function(iso) {
        startHidden.value = iso;
        startCenter = CalendarModule.parseDate(iso);
      });
    };

    const renderEnd = function() {
      CalendarModule.buildCalendar('endCalendar', 'endCalLabel', endCenter, endHidden.value, function(iso) {
        endHidden.value = iso;
        endCenter = CalendarModule.parseDate(iso);
      });
    };

    // Initial render
    renderStart();
    renderEnd();

    // Navigation buttons
    document.querySelectorAll('.calendar-nav button').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        const cal = this.dataset.cal;
        const dir = parseInt(this.dataset.dir) || 0;

        if (cal === 'start') {
          CalendarModule.navigate(startCenter, dir, renderStart);
        } else if (cal === 'end') {
          CalendarModule.navigate(endCenter, dir, renderEnd);
        }
      });
    });

    logger.log('SampleSummaryCalendar initialized');
  }

  return { init: init };
})();

// Initialize calendar on DOM ready
document.addEventListener('DOMContentLoaded', function() {
  SampleSummaryCalendar.init();
});


/* ========================================
   2. AG GRID MODULE
======================================== */

const GridModule = (function() {
  'use strict';

  // Config from HTML with safe fallbacks
  const CONFIG = (typeof LIMS_CONFIG !== 'undefined' && LIMS_CONFIG !== null) ? LIMS_CONFIG : {};
  const tableData = Array.isArray(CONFIG.samplesData) ? CONFIG.samplesData : [];
  const dynamicCols = Array.isArray(CONFIG.analysisTypes) ? CONFIG.analysisTypes : [];
  const URLS = (CONFIG.urls && typeof CONFIG.urls === 'object') ? CONFIG.urls : {};
  const I18N = (CONFIG.i18n && typeof CONFIG.i18n === 'object') ? CONFIG.i18n : {};

  // Grid instance reference
  let gridApi = null;

  // Column state storage key
  const COL_STATE_KEY = 'sample_summary_col_state_v3';

  // Precision map — backend display_precision.py-ээс ирнэ
  const PRECISION_MAP = (CONFIG.precisionMap && typeof CONFIG.precisionMap === 'object')
    ? CONFIG.precisionMap
    : {};
  const DEFAULT_PRECISION = PRECISION_MAP._default || 2;

  /* -------- UTILITY FUNCTIONS -------- */

  function safeNumber(val) {
    if (val === null || val === undefined || val === '' || val === 'null') return null;
    const str = String(val).replace(',', '').trim();
    const num = parseFloat(str);
    return isNaN(num) ? null : num;
  }

  function formatByCode(code, raw) {
    const num = safeNumber(raw);
    if (num === null) return '';
    const dp = PRECISION_MAP.hasOwnProperty(code) ? PRECISION_MAP[code] : DEFAULT_PRECISION;
    return num.toFixed(dp);
  }

  function toDateOrNull(v) {
    if (!v) return null;
    try {
      const d = new Date(String(v).replace(' ', 'T'));
      return isNaN(d.getTime()) ? null : d;
    } catch (e) {
      return null;
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /* -------- CELL RENDERERS -------- */

  function sampleNameRenderer(params) {
    if (!params.data) return '-';
    const name = escapeHtml(params.data.sample_code || params.value || '-');
    const url = escapeHtml(params.data.report_url || '#');
    const title = escapeHtml(params.data.sample_code || params.data.name || '');
    return `<a class="sample-link" href="${url}" title="${title}">${name}</a>`;
  }

  function resultValueRenderer(params) {
    // valueGetter нь тоон утга гаргадаг, гэхдээ cellRenderer-д raw data хэрэгтэй
    const data = params.data ? params.data[params.colDef.field] : null;
    const code = params.colDef.field;
    const sampleId = params.data ? params.data.id : null;

    // Empty cell - show "request analysis" button
    if (data === null || data === undefined || data === 'null' || data === '') {
      if (sampleId) {
        return `<button type="button" class="request-analysis-btn" data-sample-id="${sampleId}" data-analysis-code="${escapeHtml(code)}" title="Order analysis">+</button>`;
      }
      return '';
    }

    // Object with status and value
    if (data && typeof data === 'object') {
      const raw = (data.value !== undefined && data.value !== null && data.value !== 'null')
        ? data.value : '';
      const val = formatByCode(code, raw);
      const status = data.status || '';
      const rid = data.id || '';

      // Empty value in object - show request button
      if (!val) {
        if (sampleId) {
          return `<button type="button" class="request-analysis-btn" data-sample-id="${sampleId}" data-analysis-code="${escapeHtml(code)}" title="Order analysis">+</button>`;
        }
        return '';
      }

      let statusHtml = '';
      if (status === 'pending_review') {
        statusHtml = `<span class="badge bg-warning text-dark" style="font-size:10px;line-height:1;">${escapeHtml(val)}</span>`;
      } else {
        statusHtml = `<span class="result-value">${escapeHtml(val)}</span>`;
      }

      const rejectBtn = rid
        ? `<button type="button" class="ajax-reject-btn" data-result-id="${rid}" title="Return">↩</button>`
        : '';

      return `<div class="result-cell-wrapper" title="${escapeHtml(val)}">${statusHtml}${rejectBtn}</div>`;
    }

    // Simple value
    return formatByCode(code, data);
  }

  /* -------- DATE FILTER PARAMS -------- */

  const dateFilterParams = {
    comparator: function(filterDate, cellValue) {
      const cellDate = toDateOrNull(cellValue);
      if (!cellDate) return -1;

      const cellDay = new Date(cellDate.getFullYear(), cellDate.getMonth(), cellDate.getDate()).getTime();
      const filterDay = filterDate.getTime();

      if (cellDay === filterDay) return 0;
      return cellDay < filterDay ? -1 : 1;
    }
  };

  /* -------- HTML HEADER COMPONENT (for subscript support) -------- */

  class HtmlHeaderComponent {
    init(params) {
      this.eGui = document.createElement('div');
      this.eGui.classList.add('ag-cell-label-container');
      this.eGui.style.display = 'flex';
      this.eGui.style.alignItems = 'center';
      this.eGui.style.width = '100%';

      const label = document.createElement('span');
      label.classList.add('ag-header-cell-text');
      label.innerHTML = params.displayName;
      this.eGui.appendChild(label);

      // Sort icon support
      if (params.enableSorting) {
        this.eGui.style.cursor = 'pointer';
        this.eGui.addEventListener('click', (e) => {
          params.progressSort(e.shiftKey);
        });
      }
    }
    getGui() { return this.eGui; }
    destroy() {}
  }

  /* -------- COLUMN DEFINITIONS -------- */

  function buildColumnDefs() {
    const cols = [
      // Selection checkbox
      {
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
      },
      // ID
      {
        headerName: 'ID',
        field: 'id',
        minWidth: 50, width: 60, maxWidth: 120,
        pinned: 'left',
        sortable: true,
        filter: 'agNumberColumnFilter',
        floatingFilter: true,
        resizable: true,
        cellStyle: { textAlign: 'left' }
      },
      // Sample name
      {
        headerName: I18N.sampleName || 'Sample Name',
        field: 'name',
        cellRenderer: sampleNameRenderer,
        minWidth: 200, width: 220,
        pinned: 'left',
        sortable: true,
        filter: 'agTextColumnFilter',
        floatingFilter: true,
        suppressFloatingFilterButton: true, floatingFilterComponentParams: { debounceMs: 300 },
        resizable: true,
        tooltipValueGetter: function(p) {
          return p.data ? (p.data.sample_code || p.data.name || '') : '';
        }
      },
      // Client name
      {
        headerName: I18N.unit || 'Unit',
        field: 'client_name',
        minWidth: 100, width: 120,
        sortable: true,
        filter: 'agTextColumnFilter',
        floatingFilter: true,
        suppressFloatingFilterButton: true, floatingFilterComponentParams: { debounceMs: 300 },
        resizable: true
      },
      // Sample type
      {
        headerName: I18N.type || 'Type',
        field: 'sample_type',
        minWidth: 100, width: 120,
        sortable: true,
        filter: 'agTextColumnFilter',
        floatingFilter: true,
        suppressFloatingFilterButton: true, floatingFilterComponentParams: { debounceMs: 300 },
        resizable: true
      }
    ];

    // Add dynamic analysis columns with HTML header (subscript support)
    dynamicCols.forEach(function(col) {
      cols.push({
        headerName: col.header,
        headerComponent: HtmlHeaderComponent,
        field: col.code,
        cellRenderer: resultValueRenderer,
        // Object {value, status, id} -аас тоон утгыг гаргаж авах (filter, sort)
        valueGetter: function(params) {
          const raw = params.data ? params.data[col.code] : null;
          if (raw == null || raw === '' || raw === 'null') return null;
          if (typeof raw === 'object') return safeNumber(raw.value);
          return safeNumber(raw);
        },
        flex: 1,
        minWidth: 70,
        sortable: true,
        filter: 'agNumberColumnFilter',
        floatingFilter: false,
        resizable: true,
        cellStyle: { textAlign: 'left' },
        cellClassRules: {
          'highlight-cell': function(params) {
            return params.value != null;
          }
        }
      });
    });

    // Огнооны багануудыг хамгийн сүүлд нэмэх
    cols.push({
      headerName: I18N.registered || 'Registered',
      field: 'received_date',
      minWidth: 120, width: 130,
      sortable: true,
      filter: 'agDateColumnFilter',
      filterParams: dateFilterParams,
      floatingFilter: true,
      suppressFloatingFilterButton: true,
      resizable: true,
      valueFormatter: function(p) {
        if (!p.value) return '';
        return String(p.value).replace('T', ' ').slice(0, 16);
      }
    });

    cols.push({
      headerName: I18N.analyzed || 'Analyzed',
      field: 'analysis_date',
      minWidth: 120, width: 130,
      sortable: true,
      filter: 'agDateColumnFilter',
      filterParams: dateFilterParams,
      floatingFilter: true,
      suppressFloatingFilterButton: true,
      resizable: true,
      valueFormatter: function(p) {
        if (!p.value) return '';
        return String(p.value).replace('T', ' ').slice(0, 16);
      }
    });

    return cols;
  }

  /* -------- COLUMN STATE MANAGEMENT -------- */

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

  /* -------- REJECT BUTTON HANDLER -------- */

  function handleRejectClick(resultId) {
    if (!resultId) return;

    if (!confirm("Энэ үр дүнг буцаах уу?")) return;

    const updateUrl = (URLS.updateStatus || "/api/update_result_status") + "/" + resultId + "/rejected";

    fetch(updateUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name="csrf_token"]')?.value || ''
      }
    })
    .then(function(response) {
      if (!response.ok) {
        return response.json().then(function(data) {
          throw new Error(data.message || 'Action failed');
        });
      }
      return response.json();
    })
    .then(function() {
      alert('Үр дүн амжилттай буцаагдлаа.');
      window.location.reload();
    })
    .catch(function(error) {
      alert('Алдаа: ' + error.message);
    });
  }

  /* -------- REQUEST ANALYSIS HANDLER -------- */

  function handleRequestAnalysis(sampleId, analysisCode) {
    if (!sampleId || !analysisCode) return;

    if (!confirm("\"" + analysisCode + "\" order this analysis?")) return;

    const requestUrl = URLS.requestAnalysis || "/api/request_analysis";

    fetch(requestUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name="csrf_token"]')?.value || ''
      },
      body: JSON.stringify({
        sample_id: sampleId,
        analysis_code: analysisCode
      })
    })
    .then(function(response) {
      if (!response.ok) {
        return response.json().then(function(data) {
          throw new Error(data.message || 'Action failed');
        });
      }
      return response.json();
    })
    .then(function(data) {
      alert(data.message || 'Шинжилгээ амжилттай захиалагдлаа.');
      window.location.reload();
    })
    .catch(function(error) {
      alert('Алдаа: ' + error.message);
    });
  }

  /* -------- GRID OPTIONS -------- */

  const gridOptions = {
    columnDefs: buildColumnDefs(),
    rowData: tableData,
    defaultColDef: {
      resizable: true,
      sortable: true,
      filter: true,
      suppressHeaderMenuButton: true,
      suppressFloatingFilterButton: true
    },
    rowHeight: 28,
    headerHeight: 26,
    floatingFiltersHeight: 28,
    rowSelection: 'multiple',
    domLayout: 'normal',
    suppressHorizontalScroll: false,
    alwaysShowVerticalScroll: true,
    getRowId: function(params) {
      return String(params.data.id);
    },
    enableBrowserTooltips: true,
    tooltipShowDelay: 200,
    suppressCellFocus: true,

    onGridReady: function(params) {
      try {
        gridApi = params.api;

        // Set data
        if (tableData && tableData.length > 0) {
          if (typeof params.api.setGridOption === 'function') {
            params.api.setGridOption('rowData', tableData);
          } else if (typeof params.api.setRowData === 'function') {
            params.api.setRowData(tableData);
          }
        }

        // Restore column state after a short delay
        setTimeout(function() {
          try {
            restoreColumnState();
            if (typeof params.api.autoSizeColumns === 'function') {
              params.api.autoSizeColumns(['id']);
            }
          } catch (e) {
            logger.warn('Column restore/autosize error:', e);
          }
        }, 100);
      } catch (e) {
        logger.error('onGridReady error:', e);
      }
    },

    onFirstDataRendered: function(params) {
      try {
        if (typeof params.api.autoSizeColumns === 'function') {
          params.api.autoSizeColumns(['client_name', 'sample_type', 'received_date', 'analysis_date']);
        }
      } catch (e) {
        logger.warn('onFirstDataRendered error:', e);
      }
    },

    onColumnMoved: saveColumnState,
    onColumnPinned: saveColumnState,
    onColumnVisible: saveColumnState,
    onColumnResized: function(params) {
      if (params.finished) {
        saveColumnState();
      }
    },

    onCellClicked: function(params) {
      try {
        if (!params.event || !params.event.target) return;
        const target = params.event.target;

        // Check for reject button click
        if (target.classList && target.classList.contains('ajax-reject-btn')) {
          const resultId = target.dataset ? target.dataset.resultId : null;
          if (resultId) handleRejectClick(resultId);
        }
        // Check for request analysis button click
        else if (target.classList && target.classList.contains('request-analysis-btn')) {
          const sampleId = target.dataset ? target.dataset.sampleId : null;
          const analysisCode = target.dataset ? target.dataset.analysisCode : null;
          if (sampleId && analysisCode) handleRequestAnalysis(sampleId, analysisCode);
        }
        // Check parent elements
        else if (typeof target.closest === 'function') {
          const rejectBtn = target.closest('.ajax-reject-btn');
          if (rejectBtn && rejectBtn.dataset && rejectBtn.dataset.resultId) {
            handleRejectClick(rejectBtn.dataset.resultId);
            return;
          }
          const requestBtn = target.closest('.request-analysis-btn');
          if (requestBtn && requestBtn.dataset) {
            handleRequestAnalysis(requestBtn.dataset.sampleId, requestBtn.dataset.analysisCode);
          }
        }
      } catch (e) {
        logger.warn('onCellClicked error:', e);
      }
    }
  };

  /* -------- PUBLIC API -------- */

  function getApi() {
    return gridApi;
  }

  function getSelectedIds() {
    if (!gridApi) return [];
    return gridApi.getSelectedNodes().map(function(n) {
      return n.data.id;
    });
  }

  function exportXlsx() {
    if (!gridApi) {
      alert('Хүснэгт ачаалагдаагүй байна.');
      return;
    }
    if (typeof gridToXlsx === 'function') {
      gridToXlsx(gridApi, 'sample_summary.xlsx', 'Summary');
    } else {
      alert('Excel export боломжгүй (SheetJS ачаалагдаагүй).');
    }
  }

  function exportCsv() {
    if (!gridApi) {
      alert('Хүснэгт ачаалагдаагүй байна.');
      return;
    }

    gridApi.exportDataAsCsv({
      fileName: 'sample_summary.csv',
      processCellCallback: function(params) {
        const val = params.value;
        if (val && typeof val === 'object') {
          return val.value != null ? val.value : '';
        }
        return val != null ? val : '';
      },
      processHeaderCallback: function(params) {
        return params.column.getColDef().headerName || params.column.getColId();
      },
      suppressQuotes: false,
      columnSeparator: ','
    });
  }

  function copySelected() {
    // Grid API шалгах
    const api = gridApi || (gridOptions.api ? gridOptions.api : null);
    if (!api) {
      alert('Хүснэгт ачаалагдаагүй байна.');
      logger.error('copySelected: gridApi is null');
      return;
    }

    // Сонгосон мөрүүдийг авах
    let selectedNodes = [];
    try {
      selectedNodes = api.getSelectedNodes ? api.getSelectedNodes() : [];
    } catch (e) {
      logger.error('getSelectedNodes error:', e);
      // Fallback: getSelectedRows ашиглах
      try {
        const rows = api.getSelectedRows ? api.getSelectedRows() : [];
        if (rows.length > 0) {
          selectedNodes = rows.map(function(data, idx) {
            return { data: data };
          });
        }
      } catch (e2) {
        logger.error('getSelectedRows error:', e2);
      }
    }

    if (selectedNodes.length === 0) {
      alert("Хуулах мөрүүдээ сонгоно уу.");
      return;
    }

    // Баганууд авах
    let columns = [];
    try {
      if (api.getAllDisplayedColumns) {
        columns = api.getAllDisplayedColumns().filter(function(c) {
          return c.getColId() !== '_sel';
        });
      } else if (api.getColumns) {
        columns = api.getColumns().filter(function(c) {
          const colId = c.getColId ? c.getColId() : c.colId;
          return colId !== '_sel';
        });
      }
    } catch (e) {
      logger.error('getColumns error:', e);
    }

    // Хэрэв columns хоосон бол columnDefs-ээс авах
    if (columns.length === 0) {
      const colDefs = gridOptions.columnDefs || [];
      columns = colDefs.filter(function(cd) {
        return cd.field !== '_sel';
      }).map(function(cd) {
        return {
          getColId: function() { return cd.field; },
          getColDef: function() { return cd; }
        };
      });
    }

    // Header row
    const headerRow = columns.map(function(c) {
      const def = c.getColDef ? c.getColDef() : c;
      return (def.headerName || def.field || '').replace(/\n/g, ' ');
    }).join('\t');

    // Data rows
    const dataRows = selectedNodes.map(function(node) {
      const rowData = node.data || node;
      return columns.map(function(col) {
        const colId = col.getColId ? col.getColId() : (col.field || '');
        const val = rowData[colId];
        if (val && typeof val === 'object') {
          return (val.value != null) ? val.value : '';
        }
        return (val != null) ? val : '';
      }).join('\t');
    }).join('\n');

    const finalString = headerRow + '\n' + dataRows;

    // Clipboard руу хуулах
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(finalString)
        .then(function() {
          alert(selectedNodes.length + ' мөр амжилттай хуулагдлаа!');
        })
        .catch(function(err) {
          logger.warn('Clipboard API failed:', err);
          fallbackCopy(finalString, selectedNodes.length);
        });
    } else {
      fallbackCopy(finalString, selectedNodes.length);
    }
  }

  function fallbackCopy(text, count) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();

    try {
      document.execCommand('copy');
      alert(count + ' мөр амжилттай хуулагдлаа!');
    } catch (err) {
      alert("Хуулахад алдаа гарлаа.");
    }

    document.body.removeChild(textArea);
  }

  function init() {
    const gridDiv = document.getElementById('myGrid');
    if (!gridDiv) {
      logger.warn('Grid container #myGrid not found');
      return;
    }

    // Check if AG Grid is loaded
    if (typeof agGrid === 'undefined') {
      logger.error('AG Grid library not loaded');
      gridDiv.innerHTML = '<div style="padding:20px;color:#dc3545;">AG Grid failed to load.</div>';
      return;
    }

    try {
      // Create grid - using agGrid.createGrid for newer versions, fallback to constructor
      if (typeof agGrid.createGrid === 'function') {
        gridApi = agGrid.createGrid(gridDiv, gridOptions);
      } else if (typeof agGrid.Grid === 'function') {
        new agGrid.Grid(gridDiv, gridOptions);
      } else {
        throw new Error('AG Grid API not available');
      }
    } catch (e) {
      logger.error('Grid initialization error:', e);
      gridDiv.textContent = 'Хүснэгт үүсгэхэд алдаа: ' + e.message;
      gridDiv.style.cssText = 'padding:20px;color:#dc3545;';
    }
  }

  return {
    init: init,
    getApi: getApi,
    getSelectedIds: getSelectedIds,
    exportXlsx: exportXlsx,
    exportCsv: exportCsv,
    copySelected: copySelected,
    URLS: URLS
  };
})();


/* ========================================
   3. UI EVENT HANDLERS
======================================== */

document.addEventListener('DOMContentLoaded', function() {
  'use strict';

  // Initialize grid with error handling
  try {
    GridModule.init();
  } catch (e) {
    logger.error('Grid initialization failed:', e);
  }

  // Helper to safely add event listener
  function safeAddListener(id, eventType, handler) {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener(eventType, function(e) {
        try {
          handler.call(this, e);
        } catch (err) {
          logger.error('Event handler error for ' + id + ':', err);
        }
      });
    }
  }

  // Archive button
  safeAddListener('archiveBtn', 'click', function(e) {
    e.preventDefault();

    const ids = GridModule.getSelectedIds();
    const action = this.getAttribute('value') || this.value || 'archive';

    if (ids.length === 0) {
      alert("Архивлах дээжүүдээ сонгоно уу.");
      return;
    }

    const actionText = action === 'archive' ? 'архивлах' : 'сэргээх';
    if (!confirm('Сонгосон ' + ids.length + ' дээжийг ' + actionText + ' уу?')) {
      return;
    }

    const idsInput = document.getElementById('selected_sample_ids');
    const actionInput = document.getElementById('action_hidden');
    const form = document.getElementById('limsForm');

    if (idsInput) idsInput.value = ids.join(',');
    if (actionInput) actionInput.value = action;
    if (form) form.submit();
  });

  // Report button (PDF report generation)
  safeAddListener('reportBtn', 'click', function(e) {
    e.preventDefault();

    const ids = GridModule.getSelectedIds();
    if (ids.length === 0) {
      alert("Тайлангийн дээжүүдээ сонгоно уу.");
      return;
    }

    const btn = this;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Generating...';

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    fetch('/pdf-reports/api/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({
        lab_type: 'coal',
        sample_ids: ids,
        date_from: null,
        date_to: null
      })
    })
    .then(r => r.json())
    .then(data => {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-file-earmark-pdf"></i> Тайлан';

      if (data.success) {
        alert('Тайлан амжилттай үүслээ: ' + data.report_number);
        window.location.href = data.redirect_url;
      } else {
        alert('Алдаа: ' + (data.error || 'Тодорхойгүй'));
      }
    })
    .catch(err => {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-file-earmark-pdf"></i> Тайлан';
      alert('Сүлжээний алдаа: ' + err.message);
    });
  });

  // Export Excel button
  safeAddListener('exportXlsxBtn', 'click', function() {
    GridModule.exportXlsx();
  });

  // Export CSV button
  safeAddListener('exportCsvBtn', 'click', function() {
    GridModule.exportCsv();
  });

  // Copy button
  safeAddListener('copySelectedBtn', 'click', function() {
    GridModule.copySelected();
  });

  // QC buttons helper
  function openQcWindow(url) {
    if (!url) {
      logger.warn('QC URL not defined');
      return;
    }
    const ids = GridModule.getSelectedIds();
    if (ids.length === 0) {
      alert("Шалгах дээжүүдээ сонгоно уу.");
      return;
    }
    const params = new URLSearchParams({ ids: ids.join(',') });
    window.location.href = url + '?' + params.toString();
  }

  // QC Composite button
  safeAddListener('qcCompositeBtn', 'click', function(e) {
    e.preventDefault();
    openQcWindow(GridModule.URLS.qcComposite);
  });

  // Norm Limit button
  safeAddListener('qcNormBtn', 'click', function(e) {
    e.preventDefault();
    openQcWindow(GridModule.URLS.qcNorm);
  });

  // Correlation button
  safeAddListener('correlationBtn', 'click', function(e) {
    e.preventDefault();
    openQcWindow(GridModule.URLS.qcCorr);
  });

  // =====================================
  // SIMULATOR INTEGRATION BUTTON
  // =====================================

  safeAddListener('simulatorSendBtn', 'click', function(e) {
    e.preventDefault();

    var ids = GridModule.getSelectedIds();
    if (ids.length === 0) {
      alert("Simulator руу илгээх дээжүүдийг сонгоно уу.");
      return;
    }

    // Get selected rows data to determine client_name
    var api = GridModule.getApi();
    var selectedRows = api
      ? api.getSelectedNodes().map(function(n) { return n.data; })
      : [];

    // Separate CHPP and WTL samples
    var chppSamples = selectedRows.filter(function(r) { return r.client_name === 'CHPP'; });
    var wtlSamples = selectedRows.filter(function(r) { return r.client_name === 'WTL'; });
    var otherSamples = selectedRows.filter(function(r) {
      return r.client_name !== 'CHPP' && r.client_name !== 'WTL';
    });

    if (otherSamples.length > 0) {
      alert("Зөвхөн CHPP болон WTL дээжүүдийг Simulator руу илгээх боломжтой.\n" +
            otherSamples.length + " дээж тохирохгүй байна.");
      return;
    }

    if (chppSamples.length === 0 && wtlSamples.length === 0) {
      alert("CHPP эсвэл WTL дээж сонгоно уу.");
      return;
    }

    var msg = 'Simulator руу илгээх:\n';
    if (chppSamples.length > 0) msg += '  CHPP: ' + chppSamples.length + ' дээж\n';
    if (wtlSamples.length > 0) msg += '  WTL: ' + wtlSamples.length + ' дээж\n';
    msg += '\nИлгээх үү?';

    if (!confirm(msg)) return;

    var btn = this;
    var originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Илгээж байна...';

    var promises = [];

    // Send CHPP samples one by one
    chppSamples.forEach(function(sample) {
      var url = (GridModule.URLS.simulatorSendChpp || '/api/send_to_simulator/chpp') + '/' + sample.id;
      promises.push(
        fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name="csrf_token"]')?.value || ''
          }
        })
        .then(function(r) { return r.json(); })
        .then(function(data) { return { sample: sample.sample_code, result: data }; })
        .catch(function(err) { return { sample: sample.sample_code, error: err.message }; })
      );
    });

    // Send WTL samples by lab_number (бүх дээж)
    // Lab number: sample_code-ийн эхний хэсэг ("26_01_" гэх мэт)
    // "26_01_/+16.0/_F1.300" → "26_01_"
    // "26_01_DRY_/+16.0" → "26_01_" (DRY_/WET_ хассан)
    // "26_01_C1" → "26_01_"
    var wtlLabNumbers = {};
    wtlSamples.forEach(function(sample) {
      var code = sample.sample_code || '';
      // Lab number олох: DRY_, WET_, C1-C3, T1-T2, COMP, INITIAL хассан prefix
      var labNumber = code.replace(/(?:DRY_|WET_|COMP|INITIAL|C\d|T\d).*$/, '');
      // "/" тэмдэгтийн өмнөх хэсэг
      var slashIdx = labNumber.indexOf('/');
      if (slashIdx > 0) labNumber = labNumber.substring(0, slashIdx);
      if (labNumber) wtlLabNumbers[labNumber] = sample;
    });

    Object.keys(wtlLabNumbers).forEach(function(labNumber) {
      var url = (GridModule.URLS.simulatorSendWtl || '/api/send_to_simulator/wtl') + '/' + encodeURIComponent(labNumber);
      promises.push(
        fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name="csrf_token"]')?.value || ''
          }
        })
        .then(function(r) { return r.json(); })
        .then(function(data) { return { sample: 'WTL-' + labNumber, result: data }; })
        .catch(function(err) { return { sample: 'WTL-' + labNumber, error: err.message }; })
      );
    });

    Promise.all(promises).then(function(results) {
      btn.disabled = false;
      btn.innerHTML = originalHtml;

      var successes = results.filter(function(r) { return r.result && r.result.success; });
      var failures = results.filter(function(r) { return r.error || (r.result && r.result.error); });

      var resultMsg = 'Simulator илгээлт:\n\n';

      successes.forEach(function(s) {
        resultMsg += '✓ ' + s.sample + ': ';
        // Simulator response message харуулах
        var simResp = s.result.simulator_response;
        if (simResp && simResp.detail) {
          var parts = [];
          if (simResp.detail.fractions) parts.push(simResp.detail.fractions + ' фракц');
          if (simResp.detail.dry_screen) parts.push(simResp.detail.dry_screen + ' хуурай шигшүүр');
          if (simResp.detail.wet_screen) parts.push(simResp.detail.wet_screen + ' нойтон шигшүүр');
          if (simResp.detail.composites) parts.push(simResp.detail.composites + ' нэгдсэн');
          resultMsg += parts.join(', ') + '\n';
        } else {
          resultMsg += (s.result.message || 'Амжилттай') + '\n';
        }
      });

      if (failures.length > 0) {
        resultMsg += '\nАлдаатай: ' + failures.length + '\n';
        failures.forEach(function(f) {
          var errMsg = f.error || (f.result && f.result.error) || 'Тодорхойгүй';
          resultMsg += '✗ ' + f.sample + ': ' + errMsg + '\n';
        });
      }
      alert(resultMsg);
    });
  });
});
