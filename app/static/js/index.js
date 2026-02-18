/* ----------------------------- CALENDAR LOGIC (7-Day Rolling) ----------------------------- */
/* ✅ REFACTORED: CalendarModule ашиглаж байна (calendar-module.js) */

// CalendarModule-ийн alias (хуучин кодтой нийцтэй байх)
function toLocalISOString(date) {
    return CalendarModule.formatLocalDateTime(date);
}

function formatDateLabel(date) {
    return CalendarModule.formatDateLabel(date);
}

function buildCalendar(containerId, labelId, centerDate, selectedStr, onSelect) {
    // appendTime тохиргоог containerId-ээс тодорхойлох
    const appendTime = containerId === 'endCalendar' ? 'T23:59' : 'T00:00';
    CalendarModule.buildCalendar(containerId, labelId, centerDate, selectedStr, onSelect, { appendTime });
}

// --- MAIN SCRIPT ---
document.addEventListener('DOMContentLoaded', function() {

    // 1. Init Date Variables
    const now = new Date();
    const startDefault = new Date(now);
    const endDefault = new Date(now);

    if (now.getHours() < 6) {
        startDefault.setDate(startDefault.getDate() - 1);
        startDefault.setHours(6, 0, 0, 0);
        endDefault.setHours(5, 59, 0, 0);
    } else {
        startDefault.setHours(6, 0, 0, 0);
        endDefault.setDate(endDefault.getDate() + 1);
        endDefault.setHours(5, 59, 0, 0);
    }

    const startInput = document.getElementById('dateFilterStart');
    const endInput = document.getElementById('dateFilterEnd');

    startInput.value = toLocalISOString(startDefault);
    endInput.value = toLocalISOString(endDefault);

    let sCenter = new Date(startDefault);
    let eCenter = new Date(endDefault);

    const renderS = () => buildCalendar('startCalendar', 'startCalLabel', sCenter, startInput.value, (iso) => {
        startInput.value = iso;
        sCenter = new Date(iso);
        loadData();
    });
    const renderE = () => buildCalendar('endCalendar', 'endCalLabel', eCenter, endInput.value, (iso) => {
        endInput.value = iso;
        eCenter = new Date(iso);
        loadData();
    });

    function nav(cal, dir) {
        const shiftDays = 7 * dir;
        if (cal === 'start') { sCenter.setDate(sCenter.getDate() + shiftDays); renderS(); }
        else { eCenter.setDate(eCenter.getDate() + shiftDays); renderE(); }
    }
    document.querySelectorAll('.calendar-nav button').forEach(b => {
        b.addEventListener('click', (e) => {
            e.preventDefault(); nav(b.dataset.cal, Number(b.dataset.dir));
        });
    });

    renderS();
    renderE();


    // 2. AG GRID CONFIG
    const analysisNameMap = {
        'MT': 'Total moisture (MT)', 'Mad': 'Moisture (Mad)', 'Aad': 'Ash (Aad)', 'Vad': 'Volatile Matter (Vad)',
        'TS': 'Total sulfur (TS)', 'CV': 'Calorific value (CV)', 'FM': 'Free moisture (FM)', 'CSN': 'Crucible swelling num',
        'Gi': 'Caking index (Gi)', 'TRD': 'True relative density', 'P': 'Phosphorus (P)', 'F': 'Fluorine (F)',
        'Cl': 'Chlorine (Cl)', 'X': 'Plastometer X', 'Y': 'Plastometer Y', 'CRI': 'Coke Reactivity',
        'CSR': 'Coke Strength', 'Solid':'Solid', 'm': 'Mass'
    };

    function normalizeToBase(code) {
        if (!code) return code;
        const c = String(code).trim();
        const aliasToBase = { 'St,ad': 'TS', 'Qgr,ad': 'CV', 'TRD,d': 'TRD', 'P,ad': 'P', 'F,ad': 'F', 'Cl,ad': 'Cl' };
        return aliasToBase[c] || c;
    }
    function displayCodeAlias(baseCode) {
        const alias = { 'MT': 'MT', 'TS': 'St,ad', 'CV': 'Qgr,ad' };
        return alias[baseCode] || baseCode;
    }
    function displayNameWithAlias(baseCode) {
        const baseName = analysisNameMap[baseCode] || baseCode;
        const ali = displayCodeAlias(baseCode);
        return baseName.replace(`(${baseCode})`, `(${ali})`);
    }

    const T = (typeof LIMS_I18N !== 'undefined') ? LIMS_I18N : {};
    const columnDefs = [
        {
            headerName: '', field: 'sel',
            checkboxSelection: true, headerCheckboxSelection: true,
            width: 40, pinned: 'left', lockPosition: 'left',
            filter: false, suppressMenu: true
        },
        {
            field: '1', headerName: 'ID', width: 70, pinned: 'left',
            sortable: true,
            sort: 'asc',
            filter: 'agNumberColumnFilter'
        },
        {
            field: '2', headerName: T.sampleCode || 'Sample Code', width: 350, pinned: 'left',
            sortable: true,
            filter: 'agTextColumnFilter'
        },
        { field: '3', headerName: T.client || 'Client', width: 120, sortable: true, filter: 'agTextColumnFilter' },
        { field: '4', headerName: T.type || 'Type', width: 100, sortable: true, filter: 'agTextColumnFilter' },
        { field: '5', headerName: T.condition || 'Condition', width: 100, sortable: true, filter: 'agTextColumnFilter' },
        { field: '11', headerName: T.weightKg || 'Weight (kg)', width: 100, filter: 'agNumberColumnFilter' },
        { field: '6', headerName: T.submittedBy || 'Submitted by', width: 150, filter: 'agTextColumnFilter' },
        { field: '7', headerName: T.preparedBy || 'Prepared by', width: 150, filter: 'agTextColumnFilter' },
        { field: '8', headerName: T.preparedDate || 'Prepared date', width: 120, filter: 'agDateColumnFilter' },
        {
            field: '10', headerName: T.registered || 'Registered', width: 140,
            sortable: true,
            filter: 'agDateColumnFilter'
        },
        { field: '9', headerName: T.comment || 'Comment', width: 150, filter: 'agTextColumnFilter' },
        {
            field: '14', headerName: T.storage || 'Storage', width: 120,
            filter: false,
            cellRenderer: params => params.value || ''
        },
        {
            field: '12', headerName: T.status || 'Status', width: 120,
            filter: 'agTextColumnFilter',
            cellRenderer: params => {
                const data = params.value;
                if (data === 'approved') return `<span class="badge bg-success">${T.approved || 'Approved'}</span>`;
                if (data === 'rejected') return `<span class="badge bg-danger">${T.rejected || 'Rejected'}</span>`;
                if (data === 'pending_review') return `<span class="badge bg-warning text-dark">${T.review || 'Review'}</span>`;
                if (data === 'new') return `<span class="badge bg-info text-dark">${T.new_status || 'New'}</span>`;
                if (data === 'archived') return `<span class="badge bg-secondary">${T.archived || 'Archived'}</span>`;
                return data;
            }
        },
        { field: '15', headerName: T.action || 'Action', width: 100, filter: false, cellRenderer: p => p.value },
        {
            field: '13', headerName: T.assignments || 'Assignments', flex: 1, minWidth: 200,
            filter: 'agTextColumnFilter',
            autoHeight: true,
            hide: true,
            cellRenderer: params => {
                const data = params.value;
                if (!data || data.length <= 2) return '';
                try {
                    const analyses = JSON.parse(data);
                    if (Array.isArray(analyses) && analyses.length > 0) {
                        const badges = analyses.map(rawCode => {
                            const base = normalizeToBase(rawCode);
                            const label = displayCodeAlias(base);
                            const title = displayNameWithAlias(base);
                            return `<span class="badge bg-secondary me-1" title="${title}">${label}</span>`;
                        }).join('');
                        return `<div class="d-flex flex-wrap gap-1">${badges}</div>`;
                    }
                } catch (e) { return data; }
                return '';
            }
        }
    ];

    const gridOptions = {
        columnDefs: columnDefs,
        defaultColDef: {
            resizable: true,
            sortable: true,
            filter: true,
            floatingFilter: true,
            floatingFilterComponentParams: { suppressFilterButton: true },
            menuTabs: [],
        },
        rowSelection: 'multiple',
        animateRows: true,
        getRowId: params => params.data[1],
        domLayout: 'normal',
        overlayLoadingTemplate: '<span class="ag-overlay-loading-center">Loading...</span>',
    };

    const gridDiv = document.querySelector('#myGrid');
    new agGrid.Grid(gridDiv, gridOptions);

    function loadData() {
        gridOptions.api.showLoadingOverlay();

        const sDate = document.getElementById('dateFilterStart').value;
        const eDate = document.getElementById('dateFilterEnd').value;

        const params = new URLSearchParams({
            draw: 1,
            start: 0,
            length: 100000,
            dateFilterStart: sDate,
            dateFilterEnd: eDate
        });

        fetch(`/api/data?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                gridOptions.api.setRowData(data.data);
                gridOptions.api.hideOverlay();
            })
            .catch(error => {
                console.error('Error:', error);
                gridOptions.api.showNoRowsOverlay();
            });
    }

    document.getElementById('btnLoadData').addEventListener('click', loadData);
    document.getElementById('btnExportCsv').addEventListener('click', () => gridOptions.api.exportDataAsCsv({ fileName: 'SampleList.csv' }));

    document.getElementById('btnDeleteSelected').addEventListener('click', function() {
        // Зөвхөн одоо харагдаж байгаа (filtered) дээжүүдийг авах
        const allSelectedNodes = gridOptions.api.getSelectedNodes();
        const selectedNodes = allSelectedNodes.filter(node => node.displayed);

        if (selectedNodes.length === 0) { alert('Устгах дээжүүдийг сонгоно уу!'); return; }
        if (!confirm('Сонгосон ' + selectedNodes.length + ' дээжийг устгах уу?')) return;

        const ids = selectedNodes.map(node => node.data[1]);
        const form = document.getElementById('deleteSelectedForm');
        const oldInputs = form.querySelectorAll('input[name="sample_ids"]');
        oldInputs.forEach(i => i.remove());

        ids.forEach(id => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'sample_ids';
            input.value = id;
            form.appendChild(input);
        });
        form.submit();
    });

    // Active tab from server
    var activeTab = window.LIMS_ACTIVE_TAB || 'list-pane';
    var triggerEl = document.querySelector('button[data-bs-target="#' + activeTab + '"]');
    if (triggerEl) new bootstrap.Tab(triggerEl).show();

    loadData();
});
