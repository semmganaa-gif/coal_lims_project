/* ----------------------------- 1. CALENDAR LOGIC (Standard JS) ----------------------------- */
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
    
    if (selectedStr === isoDate) {
      td.classList.add('selected');
    }
    const isCenter = (centerDate.getDate() === dayNum && centerDate.getMonth() === currentDrawDate.getMonth());
    if (isCenter && selectedStr !== isoDate) {
       td.style.border = "1px solid var(--primary)";
    }

    td.addEventListener('click', () => {
      onSelect(isoDate);
      buildCalendar(containerId, labelId, currentDrawDate, isoDate, onSelect);
    });
    trBody.appendChild(td);
  }

  thead.appendChild(trHead);
  tbody.appendChild(trBody);
  cont.appendChild(thead);
  cont.appendChild(tbody);
}

(function() {
  const startHidden = document.getElementById('start_date_hidden');
  const endHidden = document.getElementById('end_date_hidden');
  if(!startHidden || !endHidden) return; // Prevent error on other pages

  const sVal = startHidden.value;
  const eVal = endHidden.value;
  let sCenter = sVal ? new Date(sVal.replace(/-/g, '/')) : new Date();
  let eCenter = eVal ? new Date(eVal.replace(/-/g, '/')) : new Date();

  function nav(cal, dir) {
    const shiftDays = 7 * dir; 
    if (cal === 'start') {
      sCenter.setDate(sCenter.getDate() + shiftDays);
      renderS();
    } else {
      eCenter.setDate(eCenter.getDate() + shiftDays);
      renderE();
    }
  }

  const renderS = () => buildCalendar('startCalendar', 'startCalLabel', sCenter, startHidden.value, (iso) => {
    startHidden.value = iso;
    sCenter = new Date(iso.replace(/-/g, '/')); 
  });

  const renderE = () => buildCalendar('endCalendar', 'endCalLabel', eCenter, endHidden.value, (iso) => {
    endHidden.value = iso;
    eCenter = new Date(iso.replace(/-/g, '/'));
  });

  renderS(); renderE();

  document.querySelectorAll('.calendar-nav button').forEach(b => {
    b.addEventListener('click', (e) => {
        e.preventDefault(); 
        nav(b.dataset.cal, Number(b.dataset.dir));
    });
  });
})();

/* ------------------------------ 2. AG-GRID & LOGIC ------------------------------ */

// HTML-ээс ирсэн LIMS_CONFIG-ийг ашиглана
const tableData = (typeof LIMS_CONFIG !== 'undefined') ? LIMS_CONFIG.samplesData : [];
const dynamicCols = (typeof LIMS_CONFIG !== 'undefined') ? LIMS_CONFIG.analysisTypes : [];
const URLS = (typeof LIMS_CONFIG !== 'undefined') ? LIMS_CONFIG.urls : {};

const tableRows = tableData;

function toDateOrNull(v){
  if(!v) return null;
  const d=new Date(String(v).replace(' ','T'));
  return isNaN(d)?null:d;
}
const dateFilterParams={
  comparator:(f, cv)=>{
    const d=toDateOrNull(cv);
    if(!d) return -1;
    const c=new Date(d.getFullYear(),d.getMonth(),d.getDate()).getTime();
    const ft=f.getTime();
    if(c===ft) return 0;
    return (c<ft?-1:1);
  }
};

const precisionMap={
  'MT':1,'CSN':1,'Gi':0,'X':0,'Y':0,'Qgr,ad':0,'Qgr,ar':0,'Qnet,ar':0,
  'P':3,'P,d':3,'F':3,'F,d':3,'Cl':3,'Cl,d':3
};
function formatByCode(code, raw){
  if(raw===null||raw===undefined||raw===''||raw==='null') return '';
  const n=Number(String(raw).replace(',','').trim());
  if(Number.isNaN(n)) return '';
  const dp=Object.prototype.hasOwnProperty.call(precisionMap,code)?precisionMap[code]:2;
  return n.toFixed(dp);
}

function sampleNameRenderer(p){
  const name = p.data.sample_code || p.value || '-';
  const title = p.data?.sample_code || p.data?.name || '';
  return `<a class="sample-link" href="${p.data.report_url}" title="${title}">${name}</a>`;
}

function resultValueRenderer(p){
  const data=p.value, code=p.colDef.field;
  if(data==='null'||data===null) return '';
  if(data && typeof data==='object'){
    const raw=(data.value!==undefined && data.value!==null && data.value!=='null')?data.value:'';
    const val=formatByCode(code, raw);
    const status=data.status, rid=data.id;
    if(status==='pending_review' || status==='approved'){
      return `<div class="result-cell-wrapper" title="${val}">
                ${status==='pending_review'
                  ? `<span class="badge bg-warning text-dark" style="font-size:10px;line-height:1;">${val}</span>`
                  : `<span class="result-value">${val}</span>`}
                ${rid?`<button type="button" class="ajax-reject-btn" data-result-id="${rid}" title="Буцаах">↩</button>`:''}
              </div>`;
    }
    return `<div class="result-cell-wrapper" title="${val}">
              <span class="result-value">${val}</span>
              ${rid?`<button type="button" class="ajax-reject-btn" data-result-id="${rid}" title="Буцаах">↩</button>`:''}
            </div>`;
  }
  return formatByCode(code, data);
}

// Үндсэн Баганууд
const columnDefs = [
  {
    headerName:'', field:'_sel',
    checkboxSelection:true, headerCheckboxSelection:true,
    headerCheckboxSelectionFilteredOnly:true,
    width:40,minWidth:40,maxWidth:40,
    pinned:'left',
    sortable:false, filter:false, resizable:false,
    suppressMovable:true, lockPosition:'left',
    valueGetter:p=>p.data?.id
  },
  {
    headerName:'ID', field:'id',
    minWidth:50, width:60, maxWidth:120, pinned:'left',
    sortable:true, filter:'agNumberColumnFilter',
    floatingFilter:true, resizable:true,
    cellStyle:{textAlign:'left'}
  },
  {
    headerName:'Дээжний нэр', field:'name',
    cellRenderer:sampleNameRenderer,
    minWidth:220, width:240, pinned:'left',
    sortable:true, filter:'agTextColumnFilter',
    floatingFilter:true,
    floatingFilterComponentParams:{suppressFilterButton:true, debounceMs:250},
    resizable:true, wrapText:true, autoHeight:true,
    tooltipValueGetter:p => (p.data?.sample_code || p.data?.name || ''),
    cellStyle:{lineHeight:'1.1'}
  },
  {
    headerName:'Нэгж', field:'client_name',
    minWidth:110, width:120,
    sortable:true, filter:'agTextColumnFilter',
    floatingFilter:true,
    floatingFilterComponentParams:{suppressFilterButton:true, debounceMs:250},
    resizable:true
  },
  {
    headerName:'Төрөл', field:'sample_type',
    minWidth:110, width:120,
    sortable:true, filter:'agTextColumnFilter',
    floatingFilter:true,
    floatingFilterComponentParams:{suppressFilterButton:true, debounceMs:250},
    resizable:true
  },
  {
    headerName:'Бүртгэсэн', field:'received_date',
    minWidth:130, width:140,
    sortable:true, filter:'agDateColumnFilter',
    filterParams:dateFilterParams, floatingFilter:true,
    floatingFilterComponentParams:{suppressFilterButton:true},
    resizable:true,
    valueFormatter:p=> (p.value? String(p.value).replace('T',' ').slice(0,16):'')
  },
  {
    headerName:'Шинжилсэн', field:'analysis_date',
    minWidth:130, width:140,
    sortable:true, filter:'agDateColumnFilter',
    filterParams:dateFilterParams, floatingFilter:true,
    floatingFilterComponentParams:{suppressFilterButton:true},
    resizable:true,
    valueFormatter:p=> (p.value? String(p.value).replace('T',' ').slice(0,16):'')
  }
];

// Динамик багануудыг давталтаар нэмэх
dynamicCols.forEach(col => {
    columnDefs.push({
        headerName: col.header,
        field: col.code,
        cellRenderer: resultValueRenderer,
        flex: 1, minWidth: 90,
        sortable: true, filter: 'agNumberColumnFilter',
        floatingFilter: false,
        resizable: true, movable: true,
        cellStyle: {textAlign: 'left'},
        cellClassRules: {
            'highlight-cell': (p) => {
                const v = p.value;
                if (v == null || v === '') return false;
                if (typeof v === 'object')
                    return (v.value ?? '').toString().trim() !== '';
                return v.toString().trim() !== '';
            }
        }
    });
});

const COL_STATE_KEY='sample_summary_col_state_v2';

const gridOptions = {
  columnDefs,
  rowData: tableRows,
  defaultColDef:{
    resizable:false,
    sortable:true,
    filter:true,
    suppressHeaderMenuButton:true
  },
  rowHeight:28,
  headerHeight:26,
  floatingFiltersHeight:28,
  rowSelection:'multiple',
  domLayout:'normal',
  suppressHorizontalScroll:false,
  alwaysShowVerticalScroll:true,
  alwaysShowHorizontalScroll:true,
  getRowId:p=>String(p.data.id),
  enableBrowserTooltips:true,
  tooltipShowDelay:200,
  suppressCellFocus:true,

  onGridReady(p){
    if(tableRows && tableRows.length>0) p.api.setRowData(tableRows);
    requestAnimationFrame(()=> p.columnApi.autoSizeColumns(['id'], true));
    const saved=localStorage.getItem(COL_STATE_KEY);
    if(saved){
      try{
        const st=JSON.parse(saved);
        requestAnimationFrame(()=> p.columnApi.applyColumnState({state:st, applyOrder:true}));
      }catch(e){}
    }
  },
  onFirstDataRendered:p=>{
    p.columnApi.autoSizeColumns(['client_name','sample_type','received_date','analysis_date'], true);
  },
  onGridSizeChanged:p=>{
    p.columnApi.autoSizeColumns(['client_name','sample_type','received_date','analysis_date'], true);
  },
  onColumnMoved:p=>{ localStorage.setItem(COL_STATE_KEY, JSON.stringify(p.columnApi.getColumnState())); },
  onColumnPinned:p=>{ localStorage.setItem(COL_STATE_KEY, JSON.stringify(p.columnApi.getColumnState())); },
  onColumnVisible:p=>{ localStorage.setItem(COL_STATE_KEY, JSON.stringify(p.columnApi.getColumnState())); },
  onColumnResized:p=>{ localStorage.setItem(COL_STATE_KEY, JSON.stringify(p.columnApi.getColumnState())); },

  onCellClicked(params){
    const t=params.event.target;
    // AJAX REJECT BUTTON LOGIC
    if($(t).hasClass('ajax-reject-btn') || $(t).closest('.ajax-reject-btn').length){
      const id=$(t).closest('.ajax-reject-btn').data('result-id');
      if(!confirm("Үр дүнг буцаахад итгэлтэй байна уу?")) return;
      
      const updateUrl = URLS.updateStatus || "/api/update_result_status";
      
      $.post(`${updateUrl}/${id}/rejected`)
        .done(()=>{
          alert('Үр дүн амжилттай буцаагдлаа. Хуудсыг шинэчилж байна.');
          window.location.reload();
        })
        .fail((xhr)=>{
          const m=xhr.responseJSON?xhr.responseJSON.message:'Үйлдэл амжилтгүй. API холболтыг шалгана уу.';
          alert('Алдаа: '+m);
        });
    }
  }
};

$(function(){
  const gridDiv = document.querySelector('#myGrid');
  if(gridDiv) {
      new agGrid.Grid(gridDiv, gridOptions);
  }

  $('#archiveBtn').on('click', function(e){
    e.preventDefault();
    if(!gridOptions.api) return;
    const ids=gridOptions.api.getSelectedNodes().map(n=>n.data.id);
    const action=$(this).attr('value');
    if(ids.length===0){ alert("Үйлдэл хийх дээжийг сонгоно уу."); return; }
    if(!confirm(`Сонгосон ${ids.length} дээжийг ${action==='archive'?'архивлахад':'сэргээхэд'} итгэлтэй байна уу?`)) return;
    $('#selected_sample_ids').val(ids.join(','));
    $('#action_hidden').val(action);
    $('#limsForm').submit();
  });

  $('#exportCsvBtn').on('click', function(){
    if(!gridOptions.api) return;
    const cell = (p)=> (p.value && typeof p.value==='object') ? (p.value.value??'') : (p.value??'');
    const head = (p)=> p.column.getColDef().headerName || p.column.getColId();
    gridOptions.api.exportDataAsCsv({
      fileName:'sample_summary.csv',
      processCellCallback:cell,
      processHeaderCallback:head,
      suppressQuotes:false,
      columnSeparator:','
    });
  });

  // COPY FUNCTION
  $('#copySelectedBtn').on('click', async function(){
    if(!gridOptions.api) return;
    
    const selectedNodes = gridOptions.api.getSelectedNodes();
    if (selectedNodes.length === 0) {
       alert("Хуулах мөрүүдээ сонгоно уу (Check хийнэ үү).");
       return;
    }

    const columns = gridOptions.columnApi.getAllDisplayedColumns().filter(c => c.getColId() !== '_sel');

    const headerRow = columns.map(c => {
        return (c.getColDef().headerName || c.getColId()).replace(/\n/g, ' ');
    }).join('\t');

    const dataRows = selectedNodes.map(node => {
        return columns.map(col => {
            const val = gridOptions.api.getValue(col, node);
            if (val && typeof val === 'object') {
                return (val.value !== null && val.value !== undefined) ? val.value : '';
            }
            return (val !== null && val !== undefined) ? val : '';
        }).join('\t');
    }).join('\n');

    const finalString = headerRow + '\n' + dataRows;

    try {
        await navigator.clipboard.writeText(finalString);
        alert(`${selectedNodes.length} мөр амжилттай хуулагдлаа!`);
    } catch (err) {
        // Fallback for non-secure contexts (http)
        const textArea = document.createElement("textarea");
        textArea.value = finalString;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            alert(`${selectedNodes.length} мөр амжилттай хуулагдлаа!`);
        } catch (err2) {
            console.error('Fallback copy failed', err2);
            alert("Хуулахад алдаа гарлаа.");
        }
        document.body.removeChild(textArea);
    }
  });

  /* QC BUTTONS */
  function openQcWindow(url) {
    if(!gridOptions.api) return;
    const selectedNodes = gridOptions.api.getSelectedNodes();
    if (selectedNodes.length === 0) {
      alert("Шалгах дээжүүдээ сонгоно уу.");
      return;
    }
    const ids = selectedNodes.map(n => n.data.id);
    const params = new URLSearchParams({ ids: ids.join(',') });
    window.location.href = url + '?' + params.toString();
  }

  $('#qcCompositeBtn').click(function(e){
    e.preventDefault();
    openQcWindow(URLS.qcComposite);
  });

  $('#qcSpecBtn').click(function(e){
    e.preventDefault();
    openQcWindow(URLS.qcSpec);
  });

  $('#correlationBtn').click(function(e){
    e.preventDefault();
    openQcWindow(URLS.qcCorr);
  });

});