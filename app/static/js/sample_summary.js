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
      console.warn('SampleSummaryCalendar: CalendarModule not loaded');
      return;
    }

    const startHidden = document.getElementById('start_date_hidden');
    const endHidden = document.getElementById('end_date_hidden');

    if (!startHidden || !endHidden) {
      console.log('Calendar: Hidden inputs not found, skipping init');
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

    console.log('✅ SampleSummaryCalendar initialized');
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

  // Grid instance reference
  let gridApi = null;

  // Column state storage key
  const COL_STATE_KEY = 'sample_summary_col_state_v3';

  // Precision map for formatting
  const PRECISION_MAP = {
    'MT': 1, 'CSN': 1, 'Gi': 0, 'X': 0, 'Y': 0,
    'Qgr,ad': 0, 'Qgr,ar': 0, 'Qnet,ar': 0,
    'P': 3, 'P,d': 3, 'F': 3, 'F,d': 3, 'Cl': 3, 'Cl,d': 3
  };

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
    const dp = PRECISION_MAP.hasOwnProperty(code) ? PRECISION_MAP[code] : 2;
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
      .replace(/"/g, '&quot;');
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
    const data = params.value;
    const code = params.colDef.field;
    const sampleId = params.data ? params.data.id : null;

    // Empty cell - show "request analysis" button
    if (data === null || data === undefined || data === 'null' || data === '') {
      if (sampleId) {
        return `<button type="button" class="request-analysis-btn" data-sample-id="${sampleId}" data-analysis-code="${escapeHtml(code)}" title="Шинжилгээ захиалах">+</button>`;
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
          return `<button type="button" class="request-analysis-btn" data-sample-id="${sampleId}" data-analysis-code="${escapeHtml(code)}" title="Шинжилгээ захиалах">+</button>`;
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
        ? `<button type="button" class="ajax-reject-btn" data-result-id="${rid}" title="Буцаах">↩</button>`
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
        headerName: 'Дээжний нэр',
        field: 'name',
        cellRenderer: sampleNameRenderer,
        minWidth: 200, width: 220,
        pinned: 'left',
        sortable: true,
        filter: 'agTextColumnFilter',
        floatingFilter: true,
        floatingFilterComponentParams: { suppressFilterButton: true, debounceMs: 300 },
        resizable: true,
        tooltipValueGetter: function(p) {
          return p.data ? (p.data.sample_code || p.data.name || '') : '';
        }
      },
      // Client name
      {
        headerName: 'Нэгж',
        field: 'client_name',
        minWidth: 100, width: 120,
        sortable: true,
        filter: 'agTextColumnFilter',
        floatingFilter: true,
        floatingFilterComponentParams: { suppressFilterButton: true, debounceMs: 300 },
        resizable: true
      },
      // Sample type
      {
        headerName: 'Төрөл',
        field: 'sample_type',
        minWidth: 100, width: 120,
        sortable: true,
        filter: 'agTextColumnFilter',
        floatingFilter: true,
        floatingFilterComponentParams: { suppressFilterButton: true, debounceMs: 300 },
        resizable: true
      }
    ];

    // Add dynamic analysis columns (хуучин дараалал)
    dynamicCols.forEach(function(col) {
      cols.push({
        headerName: col.header,
        field: col.code,
        cellRenderer: resultValueRenderer,
        flex: 1,
        minWidth: 80,
        sortable: true,
        filter: 'agNumberColumnFilter',
        floatingFilter: false,
        resizable: true,
        cellStyle: { textAlign: 'left' },
        cellClassRules: {
          'highlight-cell': function(params) {
            const v = params.value;
            if (v == null || v === '') return false;
            if (typeof v === 'object') {
              return (v.value != null && String(v.value).trim() !== '');
            }
            return String(v).trim() !== '';
          }
        }
      });
    });

    // Огнооны багануудыг хамгийн сүүлд нэмэх
    cols.push({
      headerName: 'Бүртгэсэн',
      field: 'received_date',
      minWidth: 120, width: 130,
      sortable: true,
      filter: 'agDateColumnFilter',
      filterParams: dateFilterParams,
      floatingFilter: true,
      floatingFilterComponentParams: { suppressFilterButton: true },
      resizable: true,
      valueFormatter: function(p) {
        if (!p.value) return '';
        return String(p.value).replace('T', ' ').slice(0, 16);
      }
    });

    cols.push({
      headerName: 'Шинжилсэн',
      field: 'analysis_date',
      minWidth: 120, width: 130,
      sortable: true,
      filter: 'agDateColumnFilter',
      filterParams: dateFilterParams,
      floatingFilter: true,
      floatingFilterComponentParams: { suppressFilterButton: true },
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

  /* -------- REJECT BUTTON HANDLER -------- */

  function handleRejectClick(resultId) {
    if (!resultId) return;

    if (!confirm("Үр дүнг буцаахад итгэлтэй байна уу?")) return;

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
          throw new Error(data.message || 'Үйлдэл амжилтгүй');
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

    if (!confirm("\"" + analysisCode + "\" шинжилгээг захиалах уу?")) return;

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
          throw new Error(data.message || 'Үйлдэл амжилтгүй');
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
      suppressHeaderMenuButton: true
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
            console.warn('Column restore/autosize error:', e);
          }
        }, 100);
      } catch (e) {
        console.error('onGridReady error:', e);
      }
    },

    onFirstDataRendered: function(params) {
      try {
        if (typeof params.api.autoSizeColumns === 'function') {
          params.api.autoSizeColumns(['client_name', 'sample_type', 'received_date', 'analysis_date']);
        }
      } catch (e) {
        console.warn('onFirstDataRendered error:', e);
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
        console.warn('onCellClicked error:', e);
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

  function exportCsv() {
    if (!gridApi) {
      alert('Grid үүсээгүй байна.');
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
      alert('Grid үүсээгүй байна.');
      console.error('copySelected: gridApi is null');
      return;
    }

    // Сонгосон мөрүүдийг авах
    let selectedNodes = [];
    try {
      selectedNodes = api.getSelectedNodes ? api.getSelectedNodes() : [];
    } catch (e) {
      console.error('getSelectedNodes error:', e);
      // Fallback: getSelectedRows ашиглах
      try {
        const rows = api.getSelectedRows ? api.getSelectedRows() : [];
        if (rows.length > 0) {
          selectedNodes = rows.map(function(data, idx) {
            return { data: data };
          });
        }
      } catch (e2) {
        console.error('getSelectedRows error:', e2);
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
      console.error('getColumns error:', e);
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
          console.warn('Clipboard API failed:', err);
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
      console.warn('Grid container #myGrid not found');
      return;
    }

    // Check if AG Grid is loaded
    if (typeof agGrid === 'undefined') {
      console.error('AG Grid library not loaded');
      gridDiv.innerHTML = '<div style="padding:20px;color:#dc3545;">AG Grid ачаалагдаагүй байна.</div>';
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
      console.error('Grid initialization error:', e);
      gridDiv.innerHTML = '<div style="padding:20px;color:#dc3545;">Grid үүсгэхэд алдаа: ' + e.message + '</div>';
    }
  }

  return {
    init: init,
    getApi: getApi,
    getSelectedIds: getSelectedIds,
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
    console.error('Grid initialization failed:', e);
  }

  // Helper to safely add event listener
  function safeAddListener(id, eventType, handler) {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener(eventType, function(e) {
        try {
          handler.call(this, e);
        } catch (err) {
          console.error('Event handler error for ' + id + ':', err);
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
      alert("Архивлах дээжийг сонгоно уу.");
      return;
    }

    const actionText = action === 'archive' ? 'архивлахад' : 'сэргээхэд';
    if (!confirm('Сонгосон ' + ids.length + ' дээжийг ' + actionText + ' итгэлтэй байна уу?')) {
      return;
    }

    const idsInput = document.getElementById('selected_sample_ids');
    const actionInput = document.getElementById('action_hidden');
    const form = document.getElementById('limsForm');

    if (idsInput) idsInput.value = ids.join(',');
    if (actionInput) actionInput.value = action;
    if (form) form.submit();
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
      console.warn('QC URL not defined');
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
  // ICPMS INTEGRATION BUTTONS
  // =====================================

  // Helper function for ICPMS API calls
  function icpmsApiCall(url, data) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name="csrf_token"]')?.value || ''
      },
      body: JSON.stringify(data)
    })
    .then(function(response) {
      if (!response.ok) {
        return response.json().then(function(data) {
          throw new Error(data.error || data.message || 'ICPMS алдаа');
        });
      }
      return response.json();
    });
  }

  // ICPMS Send Selected button
  safeAddListener('icpmsSendBtn', 'click', function(e) {
    e.preventDefault();

    const ids = GridModule.getSelectedIds();
    if (ids.length === 0) {
      alert("ICPMS руу илгээх дээжүүдийг сонгоно уу.");
      return;
    }

    if (!confirm('Сонгосон ' + ids.length + ' дээжийг ICPMS руу илгээх үү?')) {
      return;
    }

    // Disable button and show loading
    const btn = this;
    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Илгээж байна...';

    const sendUrl = GridModule.URLS.icpmsSend || '/api/icpms/send';

    icpmsApiCall(sendUrl, {
      sample_ids: ids.map(function(id) { return parseInt(id); }),
      include_washability: true
    })
    .then(function(result) {
      btn.disabled = false;
      btn.innerHTML = originalHtml;

      if (result.success) {
        let msg = 'ICPMS руу ' + result.sent_count + ' дээж амжилттай илгээгдлээ.';
        if (result.errors && result.errors.length > 0) {
          msg += '\n\nАнхааруулга:\n' + result.errors.slice(0, 3).join('\n');
          if (result.errors.length > 3) {
            msg += '\n... +' + (result.errors.length - 3) + ' алдаа';
          }
        }
        alert(msg);
      } else {
        alert('Алдаа: ' + (result.error || 'Илгээлт амжилтгүй'));
      }
    })
    .catch(function(error) {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
      alert('ICPMS холболтын алдаа: ' + error.message);
    });
  });

  // ICPMS Send CHPP button
  safeAddListener('icpmsChppBtn', 'click', function(e) {
    e.preventDefault();

    if (!confirm('CHPP нэгжийн сүүлийн 7 хоногийн батлагдсан үр дүнг ICPMS руу илгээх үү?')) {
      return;
    }

    // Disable button and show loading
    const btn = this;
    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Илгээж байна...';

    const sendUrl = GridModule.URLS.icpmsSendChpp || '/api/icpms/send-chpp';

    icpmsApiCall(sendUrl, { days_back: 7 })
    .then(function(result) {
      btn.disabled = false;
      btn.innerHTML = originalHtml;

      if (result.success || result.sent_count !== undefined) {
        let msg = result.message || ('ICPMS руу ' + result.sent_count + ' дээж илгээгдлээ.');
        if (result.errors && result.errors.length > 0) {
          msg += '\n\nАнхааруулга:\n' + result.errors.slice(0, 3).join('\n');
        }
        alert(msg);
      } else {
        alert('Алдаа: ' + (result.error || 'Илгээлт амжилтгүй'));
      }
    })
    .catch(function(error) {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
      alert('ICPMS холболтын алдаа: ' + error.message);
    });
  });
});
