// app/static/js/aggrid_helpers.js
// Нийтлэг AG Grid туслахууд: сум/Enter навигаци, alias уншигч
(function (w) {
  'use strict';

  /**
   * Editable колоннуудын жагсаалтад тулгуурлан Arrow/Enter навигаци хийдэг suppressKeyboardEvent factory.
   * (Legacy support - хуучин AG Grid хувилбаруудад)
   */
  function navHandlerFactory(editColIds) {
    const NAV_KEYS = new Set(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Enter']);
    return function navHandler(params) {
      const k = params.event.key;
      if (!NAV_KEYS.has(k)) return false;
      const api = params.api;
      const focused = api.getFocusedCell();
      if (!focused || !focused.column) return false;

      const currentColId = focused.column.getColId();
      const colIndex = editColIds.indexOf(currentColId);
      if (colIndex === -1) return false; // editable биш → default

      let nextRow = focused.rowIndex;
      let nextColIndex = colIndex;

      if (k === 'ArrowUp') nextRow = Math.max(0, nextRow - 1);
      else if (k === 'ArrowDown') nextRow = Math.min(api.getDisplayedRowCount() - 1, nextRow + 1);
      else if (k === 'ArrowLeft') nextColIndex = Math.max(0, colIndex - 1);
      else if (k === 'ArrowRight' || k === 'Enter') {
        if (colIndex === editColIds.length - 1) {
          nextRow = Math.min(api.getDisplayedRowCount() - 1, nextRow + 1);
          nextColIndex = 0;
        } else {
          nextColIndex = colIndex + 1;
        }
      }

      const nextColId = editColIds[nextColIndex];
      api.stopEditing();
      api.ensureIndexVisible(nextRow);
      api.setFocusedCell(nextRow, nextColId);
      setTimeout(() => api.startEditingCell({ rowIndex: nextRow, colKey: nextColId }), 0);
      return true;
    };
  }

  /**
   * Modern AG Grid navigation handler using navigateToNextCell callback
   * Excel-style keyboard navigation with arrow keys
   */
  function createNavigateToNextCell(editColIds) {
    return function(params) {
      const { key } = params;
      const { previousCellPosition, nextCellPosition } = params;
      const api = params.api;

      // Handle Tab/Enter to move to next editable cell
      if (key === 'Tab' || key === 'Enter') {
        const currentColId = previousCellPosition.column.getColId();
        const colIndex = editColIds.indexOf(currentColId);

        if (colIndex === -1) return nextCellPosition; // Not editable, use default

        const isLastCol = colIndex === editColIds.length - 1;
        const isLastRow = previousCellPosition.rowIndex === api.getDisplayedRowCount() - 1;

        if (isLastCol) {
          if (isLastRow) {
            // Last cell - stay here or cycle to first
            return previousCellPosition;
          }
          // Move to first editable col of next row
          return {
            rowIndex: previousCellPosition.rowIndex + 1,
            column: api.getColumnDef(editColIds[0])?.field || editColIds[0],
            rowPinned: previousCellPosition.rowPinned
          };
        }

        // Move to next editable column in same row
        return {
          rowIndex: previousCellPosition.rowIndex,
          column: editColIds[colIndex + 1],
          rowPinned: previousCellPosition.rowPinned
        };
      }

      // Default navigation for arrow keys
      return nextCellPosition;
    };
  }

  /**
   * Modern keyboard event handler for arrow key navigation in editable cells
   */
  function createCellKeyDown(editColIds) {
    return function(params) {
      const { event, api } = params;
      const key = event.key;

      if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(key)) {
        return;
      }

      const focused = api.getFocusedCell();
      if (!focused) return;

      const currentColId = focused.column.getColId();
      const colIndex = editColIds.indexOf(currentColId);

      // Only handle navigation for editable columns
      if (colIndex === -1) return;

      event.preventDefault();
      event.stopPropagation();

      let nextRow = focused.rowIndex;
      let nextColId = currentColId;

      if (key === 'ArrowUp') {
        nextRow = Math.max(0, nextRow - 1);
      } else if (key === 'ArrowDown') {
        nextRow = Math.min(api.getDisplayedRowCount() - 1, nextRow + 1);
      } else if (key === 'ArrowLeft') {
        const newColIndex = Math.max(0, colIndex - 1);
        nextColId = editColIds[newColIndex];
      } else if (key === 'ArrowRight') {
        const newColIndex = Math.min(editColIds.length - 1, colIndex + 1);
        nextColId = editColIds[newColIndex];
      }

      api.stopEditing();
      api.ensureIndexVisible(nextRow);
      api.setFocusedCell(nextRow, nextColId);

      // Start editing the next cell
      setTimeout(() => {
        api.startEditingCell({
          rowIndex: nextRow,
          colKey: nextColId
        });
      }, 0);
    };
  }

  /**
   * Weight alias уншигч (weight → m1 → mass fallback)
   */
  function pickWeight(p) {
    return p?.weight ?? p?.m1 ?? p?.mass ?? null;
  }

  // Generic number parsers/formatters
  function numParser(p) {
    const v = parseFloat(p.newValue);
    return isNaN(v) ? null : v;
  }
  const numFmt4 = p => (p.value != null) ? parseFloat(p.value).toFixed(4) : '';  // m1, m2, m3 жин
  const numFmt3 = p => (p.value != null) ? parseFloat(p.value).toFixed(3) : '';  // тохирц
  const numFmt2 = p => (p.value != null) ? parseFloat(p.value).toFixed(2) : '';  // дундаж
  const numFmt0 = p => (p.value != null) ? parseFloat(p.value).toFixed(0) : '';  // тигель, бюкс дугаар

  // Base colDef / grid options fragments
  const baseDefaultColDef = {
    sortable: false,
    resizable: true,
    editable: false,
    suppressMovable: true,
    wrapHeaderText: true,
    autoHeaderHeight: true,
  };

  const baseGridOptions = {
    theme: 'legacy',
    defaultColDef: baseDefaultColDef,
    suppressRowTransform: true,
    tooltipShowDelay: 0,
    suppressFieldDotNotation: true,
    suppressDragLeaveHidesColumns: true,
    singleClickEdit: true,
    stopEditingWhenCellsLoseFocus: true,
    enterNavigatesVertically: true,
  };

  /**
   * AG Grid үүсгэх factory function - Код давхардлыг багасгах зорилготой
   *
   * @param {string|HTMLElement} container - Grid-ийг байрлуулах element (selector эсвэл element)
   * @param {Array} columnDefs - Column definitions
   * @param {Array} rowData - Row data
   * @param {Object} customOptions - Custom grid options (optional)
   * @returns {Object} Grid API
   *
   * Жишээ:
   *   const gridApi = LIMS_AGGRID.createGrid('#myGrid', columnDefs, rowData, {
   *     onCellValueChanged: (params) => { ... },
   *     editableColIds: ['m1', 'm2', 'm3']
   *   });
   */
  function createGrid(container, columnDefs, rowData, customOptions = {}) {
    // Container element олох
    const element = typeof container === 'string'
      ? document.querySelector(container)
      : container;

    if (!element) {
      console.error('LIMS_AGGRID.createGrid: Container element not found:', container);
      return null;
    }

    // Editable column IDs-ийг авах (keyboard navigation-д хэрэгтэй)
    const editableColIds = customOptions.editableColIds ||
      columnDefs.filter(col => col.editable).map(col => col.field);

    // ✨ Modern AG Grid navigation callbacks
    const navigationCallbacks = {};
    if (editableColIds.length > 0) {
      navigationCallbacks.onCellKeyDown = createCellKeyDown(editableColIds);
      navigationCallbacks.navigateToNextCell = createNavigateToNextCell(editableColIds);
      console.log('✅ Excel-style keyboard navigation enabled for columns:', editableColIds);
    }

    // Grid options нэгтгэх
    const gridOptions = {
      ...baseGridOptions,
      columnDefs: columnDefs,
      rowData: rowData,
      enterNavigatesVerticallyAfterEdit: true,
      ...navigationCallbacks,  // ✨ Add modern navigation
      ...customOptions
    };

    // editableColIds-ийг customOptions-оос устгах (AG Grid-д хэрэггүй)
    delete gridOptions.editableColIds;

    // Grid үүсгэх
    const gridApi = agGrid.createGrid(element, gridOptions);

    return gridApi;
  }

  /**
   * Analysis form-уудын хувьд нийтлэг column span logic
   * Read-only талбаруудыг тодруулж харуулах
   */
  function createSpanningCellClassRules() {
    return {
      'ag-cell-span': params => {
        // Sample_code болон бусад read-only column-ууд span хийх
        const col = params.colDef;
        return col && !col.editable;
      }
    };
  }

  /**
   * Нийтлэг status bar config (analysis form-уудад ашиглагдана)
   */
  function getStandardStatusBar() {
    return {
      statusPanels: [
        { statusPanel: 'agTotalRowCountComponent', align: 'left' },
        { statusPanel: 'agFilteredRowCountComponent', align: 'left' },
        { statusPanel: 'agSelectedRowCountComponent', align: 'center' },
        { statusPanel: 'agAggregationComponent', align: 'right' }
      ]
    };
  }

  // Export to global
  w.LIMS_AGGRID = w.LIMS_AGGRID || {};

  // Navigation handlers
  w.LIMS_AGGRID.navHandlerFactory = navHandlerFactory;  // Legacy
  w.LIMS_AGGRID.createNavigateToNextCell = createNavigateToNextCell;  // ✨ Modern
  w.LIMS_AGGRID.createCellKeyDown = createCellKeyDown;  // ✨ Modern

  // Utilities
  w.LIMS_AGGRID.pickWeight = pickWeight;
  w.LIMS_AGGRID.numParser = numParser;
  w.LIMS_AGGRID.numFmt4 = numFmt4;  // m1, m2, m3 жин
  w.LIMS_AGGRID.numFmt3 = numFmt3;  // тохирц
  w.LIMS_AGGRID.numFmt2 = numFmt2;  // дундаж
  w.LIMS_AGGRID.numFmt0 = numFmt0;  // тигель, бюкс дугаар

  // Base configs
  w.LIMS_AGGRID.baseDefaultColDef = baseDefaultColDef;
  w.LIMS_AGGRID.baseGridOptions = baseGridOptions;

  // Grid factory
  w.LIMS_AGGRID.createGrid = createGrid;
  w.LIMS_AGGRID.createSpanningCellClassRules = createSpanningCellClassRules;
  w.LIMS_AGGRID.getStandardStatusBar = getStandardStatusBar;

  console.log('✅ LIMS AG Grid Helpers loaded (v2.0 - Modern Navigation)');
})(window);
