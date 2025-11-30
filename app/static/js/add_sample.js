// static/js/add_sample.js

document.addEventListener('DOMContentLoaded', function() {
  
  // ------------------------ 1. DATA FROM GLOBAL_DATA ------------------------
  const sampleTypeOptions = GLOBAL_DATA.sampleTypeOptions;
  const all_12h_samples = GLOBAL_DATA.all12hSamples;
  const constant_12h_samples = GLOBAL_DATA.constant12hSamples;
  const comPrimaryProducts = GLOBAL_DATA.comPrimaryProducts;
  const comSecondaryMap = GLOBAL_DATA.comSecondaryMap;
  const unitAbbreviations = GLOBAL_DATA.unitAbbreviations;

  // ------------------------ 2. HELPERS (Analysis & Date) ------------------------
  
  // Analysis names mapping
  const analysisNameMap = { 'MT':'Total moisture','Mad':'Moisture','Aad':'Ash','Vad':'Volatile','TS':'Sulfur','CV':'CV','CSN':'CSN','Gi':'Gi','TRD':'TRD','P':'Phosphorus','F':'Fluorine','Cl':'Chlorine','X':'X','Y':'Y','CRI':'CRI','CSR':'CSR' };
  function normalizeToBase(code) { if (!code) return code; const c = String(code).trim(); const a = {'St,ad':'TS','Qgr,ad':'CV','TRD,d':'TRD','P,ad':'P','F,ad':'F','Cl,ad':'Cl'}; return a[c]||c; }
  function displayCodeAlias(base) { const a = {'MT':'MT','TS':'St,ad','CV':'Qgr,ad'}; return a[base]||base; }
  function displayNameWithAlias(base) { return (analysisNameMap[base]||base).replace(`(${base})`,`(${displayCodeAlias(base)})`); }

  // Date Helper (YYYY-MM-DD)
  function getTodayString() { 
      const d=new Date(); 
      return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; 
  }
  const todayStr = getTodayString();

  // Анх ачаалахад огноонуудыг өнөөдрөөр бөглөх
  const sDateInput = document.getElementById('sample_date');
  const pDateInput = document.getElementById('prepared_date');
  if (sDateInput && !sDateInput.value) sDateInput.value = todayStr;
  if (pDateInput && !pDateInput.value) pDateInput.value = todayStr;

  // ------------------------ 3. ELEMENTS ------------------------
  const clientRadios = document.querySelectorAll('input[name="client_name"]');
  const sampleTypeContainer = document.getElementById('sample-type-container');
  const unitSpecificSections = document.querySelectorAll('.unit-specific-options');
  const entryContainer = document.getElementById('sample-entry-container');
  
  // Options Sections
  const chppSection = document.getElementById('chpp-options');
  const multiGenSection = document.getElementById('multi-gen-options');
  const productField = document.getElementById('product-field');
  const labSection = document.getElementById('lab-options');
  const wtlSection = document.getElementById('wtl-options');
  
  // Selects
  const comPrimarySelect = document.getElementById('com_primary_product');
  const comSecondarySelect = document.getElementById('com_secondary_product');
  const twohPrimarySelect = document.getElementById('twoh_primary_product');
  const twohSecondarySelect = document.getElementById('twoh_secondary_product');
  const comShiftSelect = document.getElementById('com_shift');
  const comIndexSelect = document.getElementById('com_index');

  // ------------------------ 4. DROPDOWN HELPERS ------------------------
  function initPrimaryOptions(el){ if(!el)return; el.innerHTML=''; comPrimaryProducts.forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=p;el.appendChild(o)}); }
  function refreshSecondaryOptions(pSel, sSel){ if(!pSel||!sSel)return; const v=pSel.value; const l=comSecondaryMap[v]||[]; sSel.innerHTML=''; l.forEach(x=>{const o=document.createElement('option');o.value=x;o.textContent=x;sSel.appendChild(o)}); if(l.includes('none')) sSel.selectedIndex=l.findIndex(x=>x!=='none')>=0?l.findIndex(x=>x!=='none'):0; else if(l.length) sSel.selectedIndex=0; }
  
  function init2hPrimaryOptions(){ initPrimaryOptions(twohPrimarySelect); refreshSecondaryOptions(twohPrimarySelect, twohSecondarySelect); }
  function initComPrimaryOptions(){ initPrimaryOptions(comPrimarySelect); refreshSecondaryOptions(comPrimarySelect, comSecondarySelect); }
  function refresh2hSecondaryOptions(){ refreshSecondaryOptions(twohPrimarySelect, twohSecondarySelect); }
  function refreshComSecondaryOptions(){ refreshSecondaryOptions(comPrimarySelect, comSecondarySelect); }
  function getComSuffix(){ const s=comShiftSelect?comShiftSelect.value:'day'; const i=comIndexSelect?comIndexSelect.value:''; return (s==='night'?'Ncom':'Dcom')+i; }

  // ------------------------ 5. UI UPDATE & SHIFT LOGIC ------------------------
  function updateForm() {
    const selectedClient = document.querySelector('input[name="client_name"]:checked');
    unitSpecificSections.forEach(s => s.style.display = 'none');
    
    // Reset List Area
    entryContainer.innerHTML = `<p class="text-muted small"><i>(Баруун талын тохиргоог хийгээд “Дээж үүсгэх” товчийг дарна уу)</i></p>`;
    sampleTypeContainer.innerHTML = '<small class="text-muted"><i>(Эхлээд нэгжээ сонгоно уу)</i></small>';

    if (!selectedClient) { labSection.style.display = 'block'; return; }
    const clientValue = selectedClient.value;

    // ================= SHIFT LOGIC (Ээлж) =================
    const targetClients = ["UHG-Geo", "BN-Geo", "QC", "Proc"];
    const now = new Date(); const h = now.getHours();
    const isLateDay = (h>=15 && h<19); 
    const isLateNight = (h>=3 && h<7);
    
    const pBy = document.getElementById('prepared_by');
    const pDate = document.getElementById('prepared_date');

    if (targetClients.includes(clientValue) && (isLateDay || isLateNight)) {
        // Ээлж хүлээлцэх үе: Огноо өнөөдөр, Нэр хоосон
        if (pDate) pDate.value = todayStr;
        if (pBy) { pBy.value = ""; pBy.placeholder = "Дараагийн ээлжийн ажилтан..."; }
    } else {
        // Хэвийн үе: Огноо өнөөдөр, Нэр Login хийсэн хүн
        if (pDate && !pDate.value) pDate.value = todayStr;
        if (pBy && pBy.value === "") { pBy.value = GLOBAL_DATA.currentUser || ""; pBy.placeholder = ""; }
    }
    // ======================================================

    // Populate Sample Types
    const types = sampleTypeOptions[clientValue] || [];
    let radiosHtml = '';
    types.forEach((type, idx) => {
      radiosHtml += `<div class="form-check form-check-inline small"><input class="form-check-input" type="radio" name="sample_type" value="${type}" id="st-${idx}"><label class="form-check-label" for="st-${idx}">${type}</label></div>`;
    });
    sampleTypeContainer.innerHTML = radiosHtml || '<small class="text-danger"><i>(Төрөл олдсонгүй)</i></small>';
    
    // Type Change Event
    document.querySelectorAll('#sample-type-container input').forEach(r => {
        r.addEventListener('change', updateSubOptions);
    });
    // Select first type by default
    if (types.length) {
        const firstRadio = document.querySelector('#sample-type-container input');
        if(firstRadio) firstRadio.checked = true;
    }

    // Show Specific Section
    if (clientValue === 'CHPP') { chppSection.style.display = 'block'; productField.style.display = 'none'; updateSubOptions(); }
    else if (['UHG-Geo','BN-Geo'].includes(clientValue)) { multiGenSection.style.display = 'block'; productField.style.display = 'none'; }
    else if (['QC','Proc'].includes(clientValue)) { multiGenSection.style.display = 'block'; productField.style.display = 'block'; }
    else if (clientValue === 'WTL') { wtlSection.style.display = 'block'; productField.style.display = 'none'; updateSubOptions(); }
    else if (clientValue === 'LAB') { labSection.style.display = 'block'; productField.style.display = 'none'; }
  }

  function updateSubOptions() {
      const c = document.querySelector('input[name="client_name"]:checked');
      if (!c) return;
      const tRadio = document.querySelector('#sample-type-container input:checked');
      
      // Reset Sub-sections
      document.querySelectorAll('.chpp-subtype').forEach(d=>d.style.display='none');
      document.querySelectorAll('.wtl-subtype').forEach(d=>d.style.display='none');

      if (c.value === 'CHPP') {
          if (!tRadio) return;
          const t = tRadio.value;
          if (t === '2 hourly') { document.getElementById('chpp-2-hourly-options').style.display = 'block'; init2hPrimaryOptions(); }
          else if (t === '4 hourly') document.getElementById('chpp-4-hourly-options').style.display = 'block';
          else if (t === '12 hourly') document.getElementById('chpp-12-hourly-options').style.display = 'block';
          else if (t === 'com') { document.getElementById('chpp-com-options').style.display = 'block'; initComPrimaryOptions(); }
      }
      if (c.value === 'WTL') {
          if (!tRadio) return;
          if (['WTL','Size','FL'].includes(tRadio.value)) document.getElementById('wtl-lab-number-field').style.display = 'block';
          else document.getElementById('wtl-other-field').style.display = 'block';
      }
  }

  // ------------------------ 6. GENERATE LIST FUNCTION ------------------------
  function generateSampleList() {
    const cRadio = document.querySelector('input[name="client_name"]:checked');
    if (!cRadio) { alert('Нэгж сонгоно уу!'); return; }
    const cVal = cRadio.value;
    
    // ✅ Энд стандарт input-ээс утга авч байна
    const dateVal = document.getElementById('sample_date').value; 
    if (!dateVal) { alert('Огноо сонгоно уу!'); return; }
    const fDate = dateVal.replace(/-/g, ''); // YYYY-MM-DD -> YYYYMMDD

    let samples = [];
    let listType = '';
    let requiresWeight = false;

    // ---------------- LOGIC START ----------------
    // Helper Shift Codes
    const get2hSC=()=>{const h=new Date().getHours();if(h>=7&&h<9)return'_D1';if(h>=9&&h<11)return'_D2';if(h>=11&&h<13)return'_D3';if(h>=13&&h<15)return'_D4';if(h>=15&&h<17)return'_D5';if(h>=17&&h<19)return'_D6';if(h>=19&&h<21)return'_N1';if(h>=21&&h<23)return'_N2';if(h>=23||h<1)return'_N3';if(h>=1&&h<3)return'_N4';if(h>=3&&h<5)return'_N5';if(h>=5&&h<7)return'_N6';return'';};
    const get4hSC=()=>{const h=new Date().getHours();if(h>=9&&h<12)return'_10:00';if(h>=13&&h<16)return'_14:00';if(h>=17&&h<20)return'_18:00';if(h>=21&&h<23)return'_22:00';if(h>=1&&h<4)return'_2:00';if(h>=5&&h<8)return'_6:00';return'';};
    const get12hSC=()=>{const h=new Date().getHours();return(h>=7&&h<19)?'_D':'_N';};

    if (cVal === 'CHPP') {
        const tRadio = document.querySelector('#sample-type-container input:checked');
        if (!tRadio) { alert('Төрөл сонгоно уу!'); return; }
        const tVal = tRadio.value;

        if (tVal === '2 hourly') {
            listType = 'chpp_2h'; requiresWeight = true;
            const sc = get2hSC();
            const pp = twohPrimarySelect.value; if(!pp){alert('CC сонго!');return;}
            samples.push(`${pp}_${fDate}${sc}`);
            const sp = twohSecondarySelect.value; if(sp&&sp!=='none') samples.push(`${sp}_${fDate}${sc}`);
            if(document.getElementById('chpp_2h_mod1').checked) samples.push(`PF211_${fDate}${sc}`);
            if(document.getElementById('chpp_2h_mod2').checked) samples.push(`PF221_${fDate}${sc}`);
            if(document.getElementById('chpp_2h_mod3').checked) samples.push(`PF231_${fDate}${sc}`);
        } else if (tVal === '4 hourly') {
            listType = 'chpp_4h';
            const sc = get4hSC();
            if(document.getElementById('chpp_4h_mod1').checked) samples.push(...['CF501','CF502','CF601/602'].map(s=>`${s}_${fDate}${sc}`));
            if(document.getElementById('chpp_4h_mod2').checked) samples.push(...['CF521','CF522','CF621/622'].map(s=>`${s}_${fDate}${sc}`));
            if(document.getElementById('chpp_4h_mod3').checked) samples.push(...['CF541','CF542','CF641/642'].map(s=>`${s}_${fDate}${sc}`));
        } else if (tVal === '12 hourly') {
            listType = 'chpp_12h';
            const cr = document.querySelector('#common-fields input[name="sample_condition"]:checked');
            if(!cr){alert('Төлөв сонго!');return;}
            const sc = get12hSC();
            const mods=[]; if(document.getElementById('chpp_12h_mod1').checked) mods.push('MOD I'); if(document.getElementById('chpp_12h_mod2').checked) mods.push('MOD II'); if(document.getElementById('chpp_12h_mod3').checked) mods.push('MOD III');
            const modS = mods.length ? all_12h_samples.filter(s => s.condition === cr.value && mods.includes(s.mod)) : [];
            const constS = constant_12h_samples.filter(s => s.condition === cr.value);
            // 12h samples are objects here
            samples = [...modS, ...constS].map(s => ({ name: `${s.name}_${fDate}${sc}`, label: s.name, is12h: true })); 
        } else if (tVal === 'com') {
            listType = 'chpp_com'; requiresWeight = true;
            const pp = comPrimarySelect.value; if(!pp){alert('CC сонго!');return;}
            const sfx = getComSuffix();
            const sps = Array.from(comSecondarySelect.selectedOptions).map(o=>o.value).filter(v=>v!=='none');
            const pfs = []; if(document.getElementById('com_pf211').checked) pfs.push('PF211'); if(document.getElementById('com_pf221').checked) pfs.push('PF221'); if(document.getElementById('com_pf231').checked) pfs.push('PF231');
            if(!pfs.length){alert('PF сонго!');return;}
            samples.push(`${pp}_${fDate}_${sfx}`);
            sps.forEach(s=>samples.push(`${s}_${fDate}_${sfx}`));
            pfs.forEach(p=>samples.push(`${p}_${fDate}_${sfx}`));
        }
    } else if (['UHG-Geo','BN-Geo','QC','Proc'].includes(cVal)) {
        listType = 'multi_gen'; requiresWeight = true;
        const loc = document.getElementById('location').value; if(!loc){alert('Location!');return;}
        const cnt = parseInt(document.getElementById('sample_count').value); if(!cnt){alert('Count!');return;}
        const tr = document.querySelector('#sample-type-container input:checked'); if(!tr){alert('Type!');return;}
        const prod = document.getElementById('product') ? document.getElementById('product').value : '';
        for(let i=1; i<=cnt; i++) {
            const p = [];
            if(['QC','Proc'].includes(cVal)){ p.push(loc); if(prod)p.push(prod); p.push(tr.value); }
            else { const a=unitAbbreviations[cVal]; if(a)p.push(a); p.push(tr.value, loc); }
            p.push(fDate, i);
            samples.push(p.join('_'));
        }
    } else {
        entryContainer.innerHTML = `<div class="text-center text-muted py-3 small">Энэ нэгжид автомат үүсгэгч байхгүй.</div>`; return;
    }
    // ---------------- LOGIC END ----------------

    if (samples.length === 0 && listType !== 'chpp_12h') {
       entryContainer.innerHTML = `<div class="text-center text-danger py-3 small">Дээж олдсонгүй.</div>`; return;
    }

    // 🛑 TABLE RENDER (With Editable Inputs)
    let tableHtml = `
    <div class="table-responsive">
        <table class="table table-hover table-bordered table-sm mb-0" id="sample-list-table" style="font-size: 0.85rem;">
            <thead class="table-light">
                <tr>
                    <th style="width: 30px;" class="text-center">#</th>
                    <th>Дээжний код</th>
                    <th style="width: 25%;">Шинжилгээ</th>
                    ${requiresWeight ? '<th style="width: 60px;">Жин</th>' : ''}
                    ${listType==='chpp_12h' ? '<th style="width: 30px;"><input type="checkbox" id="check-all-12h"></th>' : ''}
                </tr>
            </thead>
            <tbody>`;

    let finalSamples = []; 

    samples.forEach((item, idx) => {
        let name = (typeof item === 'string') ? item : item.name;
        let label = (typeof item === 'string') ? item : item.label;
        
        // ✅ Нэр засах боломжтой Input (12h-ээс бусад үед)
        let nameField = '';
        if (listType === 'chpp_12h') {
            nameField = `<span class="fw-bold text-primary">${label}</span>`;
        } else {
            nameField = `<input type="text" name="sample_codes" value="${name}" class="form-control form-control-sm p-1 fw-bold text-primary" style="border:none; background:transparent;" autocomplete="off">`;
        }

        tableHtml += `<tr>
            <td class="text-center text-muted align-middle">${idx+1}</td>
            <td class="align-middle">
                ${nameField}
                ${listType==='chpp_12h' ? `<input type="hidden" name="sample_codes_hidden" value="${name}">` : ''}
            </td>
            <td class="align-middle"></td> ${requiresWeight ? `<td class="align-middle"><input type="number" step="0.01" name="weights" class="form-control form-control-sm p-1 text-center" required></td>` : ''}
            ${listType==='chpp_12h' ? `<td class="align-middle text-center"><input type="checkbox" name="sample_codes" value="${name}" class="form-check-input sample-12h-check" checked></td>` : ''}
        </tr>`;
        
        finalSamples.push(name);
    });

    tableHtml += `</tbody></table></div>`;
    if(listType) tableHtml += `<input type="hidden" name="list_type" value="${listType}">`;
    
    entryContainer.innerHTML = tableHtml;

    if(listType === 'chpp_12h') {
        const ca = document.getElementById('check-all-12h');
        if(ca) ca.addEventListener('change', function(){
            document.querySelectorAll('.sample-12h-check').forEach(cb => cb.checked = ca.checked);
        });
    }

    if (finalSamples.length > 0) {
        fetchAnalysesPreview(finalSamples);
    }
  }

  // ------------------------ 7. PREVIEW FUNCTION ------------------------
  async function fetchAnalysesPreview(sampleNames) {
      const c = document.querySelector('input[name="client_name"]:checked');
      const t = document.querySelector('#sample-type-container input:checked');
      if (!c || !t) return;

      const rows = document.querySelectorAll('#sample-list-table tbody tr');
      const map = new Map();
      rows.forEach(r => {
          // Try getting value from input (editable) or check default logic
          const inp = r.querySelector('input[name="sample_codes"]');
          // If listType is 12h, inp is checkbox (value ok). If editable, inp is text (value ok).
          const val = inp ? inp.value : null;
          const cell = r.cells[2]; 
          if (val && cell) {
              map.set(val, cell);
              cell.innerHTML = '<span class="text-muted small">...</span>';
          }
      });

      try {
          const res = await fetch(GLOBAL_DATA.previewUrl, {
              method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': GLOBAL_DATA.csrfToken},
              body: JSON.stringify({ sample_names: sampleNames, client_name: c.value, sample_type: t.value })
          });
          if (!res.ok) throw new Error();
          const data = await res.json();

          for (const [name, codes] of Object.entries(data)) {
              const cell = map.get(name);
              if (cell && codes.length) {
                  const badges = codes.map(rc => {
                      const b = normalizeToBase(rc);
                      return `<span class="badge bg-secondary ms-1" style="font-size:0.7rem;" title="${displayNameWithAlias(b)}">${displayCodeAlias(b)}</span>`;
                  }).join('');
                  cell.innerHTML = badges;
              } else if (cell) {
                  cell.innerHTML = '<span class="text-muted small">-</span>';
              }
          }
      } catch (e) { console.error(e); }
  }

  // ------------------------ 8. EVENTS ------------------------
  clientRadios.forEach(r => r.addEventListener('change', updateForm));
  const genBtn = document.querySelector('.generate-btn');
  // Generate товч олон газарт байж болзошгүй тул бүгдийг сонгоно
  document.querySelectorAll('.generate-btn').forEach(btn => btn.addEventListener('click', generateSampleList));

  if(twohPrimarySelect) { init2hPrimaryOptions(); twohPrimarySelect.addEventListener('change', refresh2hSecondaryOptions); }
  if(comPrimarySelect) { initComPrimaryOptions(); comPrimarySelect.addEventListener('change', refreshComSecondaryOptions); }
  
  updateForm();
});