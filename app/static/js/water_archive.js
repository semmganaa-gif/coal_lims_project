/**
 * water_archive.js — Усны архив grid
 * Depends on: water_utils.js (WATER_UTILS global)
 * Config: WATER_ARCHIVE_CONFIG (from HTML template)
 */
(function() {
  'use strict';

  var U = window.WATER_UTILS || {};
  var formatValue = U.formatValue || function(c,v){ return v == null ? '' : String(v); };
  var formatLimit = U.formatLimit || function(l){ return ''; };
  var isOverLimit = U.isOverLimit || function(){ return false; };
  var isWithinLimit = U.isWithinLimit || function(){ return false; };
  var isDetectFail = U.isDetectFail || function(){ return false; };
  var isDetectPass = U.isDetectPass || function(){ return false; };
  var WATER_CHEM_COLUMNS = U.WATER_CHEM_COLUMNS || [];
  var MICRO_COLUMNS = U.MICRO_COLUMNS || [];

  var CONFIG = (typeof WATER_ARCHIVE_CONFIG !== 'undefined') ? WATER_ARCHIVE_CONFIG : {};
  var URLS = CONFIG.urls || {};
  var I18N = CONFIG.i18n || {};

  var gridApi = null;
  var currentType = 'water';

  var TAB_CONFIG = {
    'water': { title: '<i class="bi bi-droplet-fill" style="color:#3b82f6"></i> ' + (I18N.waterArchive || 'Water Chemistry Archive') },
    'microbiology': { title: '<i class="bi bi-bug-fill" style="color:#20c997"></i> ' + (I18N.microArchive || 'Microbiology Archive') },
    'water & micro': { title: '<i class="bi bi-layers-fill" style="color:#8b5cf6"></i> ' + (I18N.combinedArchive || 'Combined Archive') }
  };

  // Archive-д micro баганууд богино хэлбэрээр
  var ARCHIVE_MICRO_COLUMNS = [
    { code: 'cfu_avg', shortName: 'CFU', mns_limit: [null, 100], primary: true },
    { code: 'ecoli', shortName: 'E.coli', detect: true, primary: true },
    { code: 'salmonella', shortName: 'Salm', detect: true, primary: true },
    { code: 'cfu_22', shortName: '22\u00B0C', mns_limit: [null, 100] },
    { code: 'cfu_37', shortName: '37\u00B0C', mns_limit: [null, 100] },
    { code: 'air_cfu', shortName: 'AirCFU', mns_limit: [null, 3000] },
    { code: 'staph', shortName: 'S.aur', detect: true }
  ];

  function buildColumnDefs(labType) {
    var cols = [];
    var showChem = (labType === 'water' || labType === 'water & micro');
    var showMicro = (labType === 'microbiology' || labType === 'water & micro');

    // Checkbox
    cols.push({
      headerName: '', field: '_sel', checkboxSelection: true, headerCheckboxSelection: true,
      width: 40, minWidth: 40, maxWidth: 40, pinned: 'left', sortable: false, filter: false, resizable: false
    });

    // Registered date
    cols.push({
      headerName: I18N.registered || 'Registered', field: 'received_date', width: 95, minWidth: 85, pinned: 'left',
      sortable: true, filter: 'agTextColumnFilter', floatingFilter: true,
      cellStyle: { fontWeight: '600', color: '#1e40af' }
    });

    // Chem No.
    if (showChem) {
      cols.push({
        headerName: I18N.chemNo || 'Chem No.', field: 'chem_lab_id', width: 90, minWidth: 90, maxWidth: 90, pinned: 'left',
        sortable: false, filter: 'agTextColumnFilter', floatingFilter: true, resizable: false,
        cellStyle: { textAlign: 'center', fontWeight: '600', color: '#3b82f6' }
      });
    }

    // Micro No.
    if (showMicro) {
      cols.push({
        headerName: I18N.microNo || 'Micro No.', field: 'micro_lab_id', width: 95, minWidth: 95, maxWidth: 95, pinned: 'left',
        sortable: false, filter: 'agTextColumnFilter', floatingFilter: true, resizable: false,
        cellStyle: { textAlign: 'center', fontWeight: '600', color: '#10b981' }
      });
    }

    // Sample name
    cols.push({
      headerName: I18N.sampleName || 'Sample Name', field: 'sample_name', width: 340, minWidth: 280, pinned: 'left',
      sortable: true, filter: 'agTextColumnFilter', floatingFilter: true
    });

    // Chemistry columns
    if (showChem) {
      var chemChildren = [];
      for (var i = 0; i < WATER_CHEM_COLUMNS.length; i++) {
        var p = WATER_CHEM_COLUMNS[i];
        var colDef = {
          headerName: p.shortName, headerTooltip: 'MNS: ' + (formatLimit(p.mns_limit) || '-'),
          field: p.code, minWidth: 42, maxWidth: 70, sortable: false, filter: false,
          type: 'numericColumn', headerClass: 'chem-header',
          valueFormatter: (function(code) { return function(params) { return formatValue(code, params.value); }; })(p.code),
          cellClassRules: (function(limit) {
            return {
              'cell-over-limit': function(params) { return isOverLimit(limit, params.value); },
              'cell-within-limit': function(params) { return isWithinLimit(limit, params.value); },
              'cell-empty': function(params) { return params.value == null || params.value === ''; }
            };
          })(p.mns_limit)
        };
        if (!p.primary) colDef.columnGroupShow = 'open';
        chemChildren.push(colDef);
      }
      cols.push({ headerName: 'Chem \u25B8', headerClass: 'chem-header-group', marryChildren: false, children: chemChildren });
    }

    // Micro columns
    if (showMicro) {
      var microChildren = [];
      for (var j = 0; j < ARCHIVE_MICRO_COLUMNS.length; j++) {
        var m = ARCHIVE_MICRO_COLUMNS[j];
        var isDetect = !!m.detect;
        var microColDef = {
          headerName: m.shortName, field: m.code, minWidth: 40, maxWidth: 65, sortable: false, filter: false,
          headerClass: 'micro-header',
          valueFormatter: (function(code) { return function(params) { return formatValue(code, params.value); }; })(m.code),
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
          })(m.mns_limit)
        };
        if (!m.primary) microColDef.columnGroupShow = 'open';
        microChildren.push(microColDef);
      }
      cols.push({ headerName: 'Micro \u25B8', headerClass: 'micro-header-group', marryChildren: false, children: microChildren });
    }

    return cols;
  }

  function setGridData(rows) {
    if (!gridApi) return;
    try {
      if (typeof gridApi.setGridOption === 'function') {
        gridApi.setGridOption('rowData', rows);
      } else if (typeof gridApi.setRowData === 'function') {
        gridApi.setRowData(rows);
      }
    } catch (e) {
      logger.error('Grid setData error:', e);
    }
  }

  function updateColumns(labType) {
    if (!gridApi) return;
    var newCols = buildColumnDefs(labType);
    try {
      if (typeof gridApi.setGridOption === 'function') {
        gridApi.setGridOption('columnDefs', newCols);
      } else if (typeof gridApi.setColumnDefs === 'function') {
        gridApi.setColumnDefs(newCols);
      }
    } catch (e) {
      logger.error('Update columns error:', e);
    }
  }

  function loadData(labType) {
    currentType = labType || 'water';
    var url = (URLS.archiveData || '/labs/water-lab/chemistry/api/archive_data') + '?lab_type=' + encodeURIComponent(currentType);
    document.getElementById('rowCount').textContent = '...';

    updateColumns(currentType);

    fetch(url)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        document.getElementById('totalCount').textContent = data.total_count || 0;
        document.getElementById('waterCount').textContent = data.water_count || 0;
        document.getElementById('microCount').textContent = data.micro_count || 0;
        document.getElementById('combinedCount').textContent = data.combined_count || 0;
        document.getElementById('rowCount').textContent = (data.rows || []).length;
        document.getElementById('gridTitle').innerHTML = (TAB_CONFIG[currentType] || TAB_CONFIG['water']).title;
        // MNS limits серверээс merge
        if (data.chem_params && U.mergeMnsLimits) {
          U.mergeMnsLimits(data.chem_params);
          updateColumns(currentType);
        }
        setGridData(data.rows || []);
        setTimeout(function() { if (gridApi) { try { gridApi.autoSizeAllColumns(); } catch(e){} } }, 100);
      })
      .catch(function(err) {
        logger.error('Load error:', err);
        document.getElementById('rowCount').textContent = '0';
      });
  }

  function getSelectedIds() {
    if (!gridApi) return [];
    return gridApi.getSelectedNodes().map(function(n) { return n.data.sample_id; });
  }

  function exportCsv() {
    if (!gridApi) return;
    gridApi.exportDataAsCsv({
      fileName: 'water_archive_' + currentType.replace(/ /g, '_') + '_' + new Date().toISOString().slice(0,10) + '.csv'
    });
  }

  function copySelected() {
    if (!gridApi) return;
    var nodes = gridApi.getSelectedNodes();
    if (nodes.length === 0) { alert(I18N.selectRowsCopy || 'Please select rows to copy.'); return; }
    var columns = gridApi.getAllDisplayedColumns().filter(function(c) { return c.getColId() !== '_sel'; });
    var header = columns.map(function(c) { return c.getColDef().headerName || ''; }).join('\t');
    var dataRows = nodes.map(function(n) { return columns.map(function(c) { var v = n.data[c.getColId()]; return v != null ? v : ''; }).join('\t'); }).join('\n');
    if (navigator.clipboard) navigator.clipboard.writeText(header + '\n' + dataRows).then(function() { alert(nodes.length + ' ' + (I18N.rowsCopied || 'rows copied!')); });
  }

  document.addEventListener('DOMContentLoaded', function() {
    var gridDiv = document.getElementById('waterArchiveGrid');
    if (!gridDiv) return;

    var gridOptions = {
      columnDefs: buildColumnDefs('water'),
      rowData: [],
      defaultColDef: { resizable: true, sortable: true, filter: true, suppressHeaderMenuButton: true, suppressFloatingFilterButton: true },
      rowHeight: 28, headerHeight: 32, groupHeaderHeight: 28, floatingFiltersHeight: 28,
      rowSelection: 'multiple', suppressCellFocus: true,
      getRowId: function(p) { return String(p.data.sample_id); },
      onGridReady: function(params) { gridApi = params.api; loadData('water'); }
    };

    try {
      if (typeof agGrid.createGrid === 'function') {
        agGrid.createGrid(gridDiv, gridOptions);
      } else {
        new agGrid.Grid(gridDiv, gridOptions);
      }
    } catch (e) {
      var _esc = function(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); };
      gridDiv.innerHTML = '<div style="padding:40px;text-align:center;color:#dc3545;">Grid error: ' + _esc(e.message) + '</div>';
    }

    // Tab handlers
    var tabBtns = document.querySelectorAll('.archive-tabs .nav-link');
    for (var i = 0; i < tabBtns.length; i++) {
      tabBtns[i].addEventListener('click', function() {
        var allBtns = document.querySelectorAll('.archive-tabs .nav-link');
        for (var j = 0; j < allBtns.length; j++) allBtns[j].classList.remove('active');
        this.classList.add('active');
        loadData(this.dataset.type);
      });
    }

    // Button handlers
    var btnExport = document.getElementById('btnExportCsv');
    var btnCopy = document.getElementById('btnCopy');
    var btnRefresh = document.getElementById('btnRefresh');
    var btnUnarchive = document.getElementById('btnUnarchive');

    if (btnExport) btnExport.addEventListener('click', exportCsv);
    if (btnCopy) btnCopy.addEventListener('click', copySelected);
    if (btnRefresh) btnRefresh.addEventListener('click', function() { loadData(currentType); });
    if (btnUnarchive) {
      btnUnarchive.addEventListener('click', function() {
        var ids = getSelectedIds();
        if (ids.length === 0) { alert(I18N.selectSamples || 'Please select samples to restore.'); return; }
        if (!confirm((I18N.restoreConfirm || 'Restore selected') + ' ' + ids.length + ' ' + (I18N.samples || 'samples?'))) return;
        document.getElementById('unarchiveSampleIds').value = ids.join(',');
        document.getElementById('unarchiveForm').submit();
      });
    }
  });
})();
