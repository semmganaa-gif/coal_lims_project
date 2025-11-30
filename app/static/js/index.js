/* ----------------------------- CALENDAR LOGIC (7-Day Rolling) ----------------------------- */
function toLocalISOString(date) {
    var y = date.getFullYear();
    var m = (date.getMonth() + 1).toString().padStart(2, '0');
    var d = date.getDate().toString().padStart(2, '0');
    var h = date.getHours().toString().padStart(2, '0');
    var min = date.getMinutes().toString().padStart(2, '0');
    return `${y}-${m}-${d}T${h}:${min}`;
}

function formatDateLabel(date) {
    const y = date.getFullYear();
    const m = date.getMonth();
    const months = ["1-р сар", "2-р сар", "3-р сар", "4-р сар", "5-р сар", "6-р сар", "7-р сар", "8-р сар", "9-р сар", "10-р сар", "11-р сар", "12-р сар"];
    return months[m] + " " + y;
}

function buildCalendar(containerId, labelId, centerDate, selectedStr, onSelect) {
    const cont = document.getElementById(containerId);
    const label = document.getElementById(labelId);
    cont.innerHTML = "";
    label.textContent = formatDateLabel(centerDate);

    let startDate = new Date(centerDate);
    startDate.setDate(centerDate.getDate() - 3);

    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');
    const trHead = document.createElement('tr');
    const trBody = document.createElement('tr');
    const weekDays = ["Ня", "Да", "Мя", "Лх", "Пү", "Ба", "Бя"];

    for (let i = 0; i < 7; i++) {
        let currentDrawDate = new Date(startDate);
        currentDrawDate.setDate(startDate.getDate() + i);

        const dayNum = currentDrawDate.getDate();
        const dayName = weekDays[currentDrawDate.getDay()];

        const y = currentDrawDate.getFullYear();
        const m = String(currentDrawDate.getMonth() + 1).padStart(2, '0');
        const d = String(dayNum).padStart(2, '0');
        const isoDate = `${y}-${m}-${d}`;

        const th = document.createElement('th');
        th.textContent = dayName;
        trHead.appendChild(th);

        const td = document.createElement('td');
        td.textContent = dayNum;
        td.className = "calendar-day";

        if (selectedStr && selectedStr.startsWith(isoDate)) {
            td.classList.add('selected');
        }

        td.addEventListener('click', () => {
            let timePart = 'T00:00';
            if (containerId === 'endCalendar') timePart = 'T23:59';
            onSelect(isoDate + timePart);
            buildCalendar(containerId, labelId, currentDrawDate, isoDate + timePart, onSelect);
        });
        trBody.appendChild(td);
    }
    thead.appendChild(trHead);
    tbody.appendChild(trBody);
    cont.appendChild(thead);
    cont.appendChild(tbody);
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
        'CSR': 'Coke Strength', 'Solid':'Solid', 'm': 'Масс'
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
            // ✅ ЗАСВАР: ID баганаар автоматаар өсөхөөр (asc) эрэмбэлнэ
            sort: 'asc',
            filter: 'agNumberColumnFilter'
        },
        {
            field: '2', headerName: 'Дээжний код', width: 180, pinned: 'left',
            sortable: true,
            filter: 'agTextColumnFilter'
        },
        { field: '3', headerName: 'Захиалагч', width: 120, sortable: true, filter: 'agTextColumnFilter' },
        { field: '4', headerName: 'Төрөл', width: 100, sortable: true, filter: 'agTextColumnFilter' },
        { field: '5', headerName: 'Төлөв', width: 100, sortable: true, filter: 'agTextColumnFilter' },
        { field: '6', headerName: 'Хүлээлгэн өгсөн', width: 150, filter: 'agTextColumnFilter' },
        { field: '7', headerName: 'Бэлтгэсэн', width: 150, filter: 'agTextColumnFilter' },
        { field: '8', headerName: 'Бэлдсэн огноо', width: 120, filter: 'agDateColumnFilter' },
        { field: '9', headerName: 'Тайлбар', width: 150, filter: 'agTextColumnFilter' },
        {
            field: '10', headerName: 'Бүртгэсэн', width: 140,
            sortable: true,
            // ✅ ЗАСВАР: Бүртгэсэн огноо нь дээр нь ID эрэмбээ дагаад зөв харагдана.
            // Хэрэв огноогоор нь ялгамаар байвал энд sort: 'asc' хийж болно.
            filter: 'agDateColumnFilter'
        },
        { field: '11', headerName: 'Жин (кг)', width: 100, filter: 'agNumberColumnFilter' },
        {
            field: '12', headerName: 'Статус', width: 120,
            filter: 'agTextColumnFilter',
            cellRenderer: params => {
                const data = params.value;
                if (data === 'approved') return '<span class="badge bg-success">Approved</span>';
                if (data === 'rejected') return '<span class="badge bg-danger">Rejected</span>';
                if (data === 'pending_review') return '<span class="badge bg-warning text-dark">Review</span>';
                if (data === 'new') return '<span class="badge bg-info text-dark">New</span>';
                if (data === 'archived') return '<span class="badge bg-secondary">Archived</span>';
                return data;
            }
        },
        {
            field: '13', headerName: 'Даалгавар', flex: 1, minWidth: 200,
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
        },
        { field: '14', headerName: 'Үйлдэл', width: 100, filter: false, cellRenderer: p => p.value }
    ];

    const gridOptions = {
        columnDefs: columnDefs,
        defaultColDef: {
            resizable: true,
            sortable: true,
            filter: true,
            floatingFilter: true,
            menuTabs: ['filterMenuTab'],
        },
        rowSelection: 'multiple',
        animateRows: true,
        getRowId: params => params.data[1],
        domLayout: 'normal',
        overlayLoadingTemplate: '<span class="ag-overlay-loading-center">Ачаалж байна...</span>',
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
        const selectedNodes = gridOptions.api.getSelectedNodes();
        if (selectedNodes.length === 0) { alert('Устгах дээжээ сонгоно уу!'); return; }
        if (!confirm('Сонгосон ' + selectedNodes.length + ' дээжийг устгахдаа итгэлтэй байна уу?')) return;

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
