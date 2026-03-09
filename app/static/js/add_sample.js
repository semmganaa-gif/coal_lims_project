// static/js/add_sample.js - Hub + 50/50 Layout Version

document.addEventListener('DOMContentLoaded', function() {

  // ------------------------ 1. DATA FROM GLOBAL_DATA ------------------------
  const sampleTypeOptions = GLOBAL_DATA.sampleTypeOptions;
  const all_12h_samples = GLOBAL_DATA.all12hSamples;
  const constant_12h_samples = GLOBAL_DATA.constant12hSamples;
  const comPrimaryProducts = GLOBAL_DATA.comPrimaryProducts;
  const comSecondaryMap = GLOBAL_DATA.comSecondaryMap;
  const unitAbbreviations = GLOBAL_DATA.unitAbbreviations;

  // ------------------------ 2. HELPERS ------------------------
  const analysisNameMap = { 'MT':'Total moisture','Mad':'Moisture','Aad':'Ash','Vad':'Volatile','TS':'Sulfur','CV':'CV','CSN':'CSN','Gi':'Gi','TRD':'TRD','P':'Phosphorus','F':'Fluorine','Cl':'Chlorine','X':'X','Y':'Y','CRI':'CRI','CSR':'CSR' };
  function normalizeToBase(code) { if (!code) return code; const c = String(code).trim(); const a = {'St,ad':'TS','Qgr,ad':'CV','TRD,d':'TRD','P,ad':'P','F,ad':'F','Cl,ad':'Cl'}; return a[c]||c; }
  function displayCodeAlias(base) { const a = {'MT':'MT','TS':'St,ad','CV':'Qgr,ad'}; return a[base]||base; }
  function displayNameWithAlias(base) { return (analysisNameMap[base]||base).replace(`(${base})`,`(${displayCodeAlias(base)})`); }
  function escapeAttr(s) { return String(s || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/'/g,'&#39;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  // Ээлжийн огноо - шөнийн ээлж (0:00-7:00) өмнөх өдрийн огноотой
  function getShiftDate() {
    const d = new Date();
    const h = d.getHours();
    // Шөнийн ээлж (0:00-6:59) бол өчигдрийн огноо
    if (h < 7) {
      d.setDate(d.getDate() - 1);
    }
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  }
  const todayStr = getShiftDate();

  // Init dates
  const sDateInput = document.getElementById('sample_date');
  const pDateInput = document.getElementById('prepared_date');
  if (sDateInput && !sDateInput.value) sDateInput.value = todayStr;
  if (pDateInput && !pDateInput.value) pDateInput.value = todayStr;

  // ------------------------ 3. ELEMENTS ------------------------
  const sampleTypeContainer = document.getElementById('sample-type-container');
  const entryContainer = document.getElementById('sample-entry-container');
  const sampleCountBadge = document.getElementById('sample-count-badge');

  // Unit Options Sections
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

  // ------------------------ 5. UI UPDATE FUNCTIONS ------------------------

  function hideAllUnitOptions() {
    [chppSection, multiGenSection, wtlSection, labSection].forEach(s => {
      if(s) s.classList.remove('active');
    });
    document.querySelectorAll('.chpp-subtype').forEach(d => d.style.display = 'none');
    document.querySelectorAll('.wtl-subtype').forEach(d => d.style.display = 'none');
  }

  function showEmptyState() {
    entryContainer.innerHTML = `
      <div class="sample-list-empty">
        <i class="bi bi-inbox"></i>
        <h4>No samples registered</h4>
        <p>Click the "Create Sample" button</p>
      </div>
    `;
    if(sampleCountBadge) sampleCountBadge.textContent = '0 samples';
  }

  // Main update function - called when unit is selected from hub
  window.updateForm = function() {
    const selectedClient = document.querySelector('input[name="client_name"]:checked');
    hideAllUnitOptions();
    showEmptyState();

    if (!selectedClient) {
      sampleTypeContainer.innerHTML = '<span style="color: var(--text-muted); font-size: 0.78rem;">No unit selected</span>';
      return;
    }

    const clientValue = selectedClient.value;

    // ================= SHIFT LOGIC (Ээлж) =================
    const targetClients = ["UHG-Geo", "BN-Geo", "QC", "Proc"];
    const now = new Date(); const h = now.getHours();
    const isLateDay = (h>=15 && h<19);
    const isLateNight = (h>=3 && h<7);

    const pBy = document.getElementById('prepared_by');
    const pDate = document.getElementById('prepared_date');

    if (targetClients.includes(clientValue) && (isLateDay || isLateNight)) {
      if (pDate) pDate.value = todayStr;
      if (pBy) { pBy.value = ""; pBy.placeholder = "Next shift..."; }
    } else {
      if (pDate && !pDate.value) pDate.value = todayStr;
      if (pBy && pBy.value === "") { pBy.value = GLOBAL_DATA.currentUser || ""; pBy.placeholder = ""; }
    }

    // Populate Sample Types as chips
    const types = sampleTypeOptions[clientValue] || [];
    let chipsHtml = '';
    types.forEach((type, idx) => {
      chipsHtml += `
        <div class="type-chip">
          <input type="radio" name="sample_type" value="${escapeAttr(type)}" id="st-${idx}">
          <label class="type-chip-label" for="st-${idx}">${escapeAttr(type)}</label>
        </div>
      `;
    });
    sampleTypeContainer.innerHTML = chipsHtml || '<span style="color: #ef4444; font-size: 0.78rem;">No types found</span>';

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
    if (clientValue === 'CHPP') {
      if(chppSection) chppSection.classList.add('active');
      if(productField) productField.style.display = 'none';
      updateSubOptions();
    }
    else if (['UHG-Geo','BN-Geo'].includes(clientValue)) {
      if(multiGenSection) multiGenSection.classList.add('active');
      if(productField) productField.style.display = 'none';
    }
    else if (['QC','Proc'].includes(clientValue)) {
      if(multiGenSection) multiGenSection.classList.add('active');
      if(productField) productField.style.display = 'block';
    }
    else if (clientValue === 'WTL') {
      if(wtlSection) wtlSection.classList.add('active');
      if(productField) productField.style.display = 'none';
      updateSubOptions();
    }
    else if (clientValue === 'LAB') {
      if(labSection) labSection.classList.add('active');
      if(productField) productField.style.display = 'none';
    }
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
      else if (tRadio.value === 'MG') document.getElementById('wtl-mg-field').style.display = 'block';
      else document.getElementById('wtl-other-field').style.display = 'block';
    }
  }

  // ------------------------ 5b. WTL MG PREVIEW ------------------------
  function updateMgPreview() {
    const mod = document.getElementById('wtl_module');
    const sup = document.getElementById('wtl_supplier');
    const veh = document.getElementById('wtl_vehicle');
    const preview = document.getElementById('wtl_mg_preview');
    const dateInput = document.getElementById('sample_date');
    if (!mod || !preview) return;

    const modVal = mod.value || '';
    const supVal = (sup ? sup.value : '').trim();
    const vehVal = (veh ? veh.value : '').trim();
    const dateVal = dateInput ? dateInput.value.replace(/-/g, '') : '';

    const parts = ['MG', modVal, supVal, dateVal, vehVal].filter(p => p);
    preview.value = parts.join('_');
  }

  // Attach MG field listeners
  ['wtl_module','wtl_supplier','wtl_vehicle'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateMgPreview);
    if (el) el.addEventListener('change', updateMgPreview);
  });
  const mgDateEl = document.getElementById('sample_date');
  if (mgDateEl) mgDateEl.addEventListener('change', updateMgPreview);

  // ------------------------ 6. GENERATE LIST FUNCTION ------------------------
  function generateSampleList() {
    const cRadio = document.querySelector('input[name="client_name"]:checked');
    if (!cRadio) { showAlert('Нэгжээ сонгоно уу!'); return; }
    const cVal = cRadio.value;

    const dateVal = document.getElementById('sample_date').value;
    if (!dateVal) { showAlert('Огноо сонгоно уу!'); return; }
    const fDate = dateVal.replace(/-/g, '');

    let samples = [];
    let listType = '';
    let requiresWeight = false;
    let isChpp = (cVal === 'CHPP');

    // Shift Code Helpers
    const get2hSC=()=>{const h=new Date().getHours();if(h>=7&&h<9)return'_D1';if(h>=9&&h<11)return'_D2';if(h>=11&&h<13)return'_D3';if(h>=13&&h<15)return'_D4';if(h>=15&&h<17)return'_D5';if(h>=17&&h<19)return'_D6';if(h>=19&&h<21)return'_N1';if(h>=21&&h<23)return'_N2';if(h>=23||h<1)return'_N3';if(h>=1&&h<3)return'_N4';if(h>=3&&h<5)return'_N5';if(h>=5&&h<7)return'_N6';return'';};
    const get4hSC=()=>{const h=new Date().getHours();if(h>=9&&h<12)return'_10:00';if(h>=13&&h<16)return'_14:00';if(h>=17&&h<20)return'_18:00';if(h>=21&&h<23)return'_22:00';if(h>=1&&h<4)return'_2:00';if(h>=5&&h<8)return'_6:00';return'';};
    const get12hSC=()=>{const h=new Date().getHours();return(h>=7&&h<19)?'_D':'_N';};

    // For CHPP grouping
    let groupedSamples = {};

    if (cVal === 'CHPP') {
      const tRadio = document.querySelector('#sample-type-container input:checked');
      if (!tRadio) { showAlert('Төрлөө сонгоно уу!'); return; }
      const tVal = tRadio.value;

      if (tVal === '2 hourly') {
        listType = 'chpp_2h'; requiresWeight = true;
        const sc = get2hSC();
        const pp = twohPrimarySelect.value; if(!pp){showAlert('CC сонгоно уу!');return;}

        // Group by CC/TC and Modules
        groupedSamples['CC'] = [`${pp}_${fDate}${sc}`];
        const sp = twohSecondarySelect.value;
        if(sp && sp !== 'none') {
          groupedSamples['TC'] = [`${sp}_${fDate}${sc}`];
        }

        if(document.getElementById('chpp_2h_mod1').checked) {
          if(!groupedSamples['MOD I']) groupedSamples['MOD I'] = [];
          groupedSamples['MOD I'].push(`PF211_${fDate}${sc}`);
        }
        if(document.getElementById('chpp_2h_mod2').checked) {
          if(!groupedSamples['MOD II']) groupedSamples['MOD II'] = [];
          groupedSamples['MOD II'].push(`PF221_${fDate}${sc}`);
        }
        if(document.getElementById('chpp_2h_mod3').checked) {
          if(!groupedSamples['MOD III']) groupedSamples['MOD III'] = [];
          groupedSamples['MOD III'].push(`PF231_${fDate}${sc}`);
        }

      } else if (tVal === '4 hourly') {
        listType = 'chpp_4h';
        const sc = get4hSC();

        if(document.getElementById('chpp_4h_mod1').checked) {
          groupedSamples['MOD I'] = ['CF501','CF502','CF601/602'].map(s=>`${s}_${fDate}${sc}`);
        }
        if(document.getElementById('chpp_4h_mod2').checked) {
          groupedSamples['MOD II'] = ['CF521','CF522','CF621/622'].map(s=>`${s}_${fDate}${sc}`);
        }
        if(document.getElementById('chpp_4h_mod3').checked) {
          groupedSamples['MOD III'] = ['CF541','CF542','CF641/642'].map(s=>`${s}_${fDate}${sc}`);
        }

      } else if (tVal === '12 hourly') {
        listType = 'chpp_12h';
        const cr = document.querySelector('.condition-toggle input:checked');
        if(!cr){showAlert('Нөхцөл сонгоно уу!');return;}
        const sc = get12hSC();
        const mods=[];
        if(document.getElementById('chpp_12h_mod1').checked) mods.push('MOD I');
        if(document.getElementById('chpp_12h_mod2').checked) mods.push('MOD II');
        if(document.getElementById('chpp_12h_mod3').checked) mods.push('MOD III');

        // Group by module
        mods.forEach(mod => {
          const modSamples = all_12h_samples.filter(s => s.condition === cr.value && s.mod === mod);
          if(modSamples.length) {
            groupedSamples[mod] = modSamples.map(s => ({ name: `${s.name}_${fDate}${sc}`, label: s.name }));
          }
        });

        // Constant samples
        const constS = constant_12h_samples.filter(s => s.condition === cr.value);
        if(constS.length) {
          groupedSamples['Constant'] = constS.map(s => ({ name: `${s.name}_${fDate}${sc}`, label: s.name }));
        }

      } else if (tVal === 'com') {
        listType = 'chpp_com'; requiresWeight = true;
        const pp = comPrimarySelect.value; if(!pp){showAlert('CC сонгоно уу!');return;}
        const sfx = getComSuffix();
        const sps = Array.from(comSecondarySelect.selectedOptions).map(o=>o.value).filter(v=>v!=='none');
        const pfs = [];
        if(document.getElementById('com_pf211').checked) pfs.push('PF211');
        if(document.getElementById('com_pf221').checked) pfs.push('PF221');
        if(document.getElementById('com_pf231').checked) pfs.push('PF231');
        if(!pfs.length){showAlert('PF сонгоно уу!');return;}

        groupedSamples['CC'] = [`${pp}_${fDate}_${sfx}`];
        if(sps.length) {
          groupedSamples['TC'] = sps.map(s => `${s}_${fDate}_${sfx}`);
        }
        groupedSamples['PF'] = pfs.map(p => `${p}_${fDate}_${sfx}`);
      }

      // Flatten for count
      Object.values(groupedSamples).forEach(arr => {
        arr.forEach(item => samples.push(typeof item === 'string' ? item : item.name));
      });

    } else if (['UHG-Geo','BN-Geo','QC','Proc'].includes(cVal)) {
      listType = 'multi_gen'; requiresWeight = true;
      const tr = document.querySelector('#sample-type-container input:checked'); if(!tr){showAlert('Төрөл сонгоно уу!');return;}
      const loc = document.getElementById('location').value;
      // QC бүх төрөлд байршил заавал биш
      if(!loc && cVal !== 'QC'){showAlert('Байршил оруулна уу!');return;}
      const cnt = parseInt(document.getElementById('sample_count').value); if(!cnt){showAlert('Тоо ширхэг оруулна уу!');return;}
      const prod = document.getElementById('product') ? document.getElementById('product').value : '';
      for(let i=1; i<=cnt; i++) {
        let sampleCode;
        if(cVal === 'QC' && tr.value === 'Fine'){
          // QC Fine: ECO_20251202_1 формат (байршил хэрэггүй)
          if(!prod){showAlert('Бүтээгдэхүүн оруулна уу!');return;}
          sampleCode = `${prod}_${fDate}_${i}`;
        } else if(cVal === 'QC'){
          // QC (Fine-ээс бусад): байршил байвал loc_prod_type, байхгүй бол prod_type
          const p = [];
          if(loc) p.push(loc);
          if(prod) p.push(prod);
          p.push(tr.value, fDate, i);
          sampleCode = p.join('_');
        } else if(cVal === 'Proc'){
          // Proc: loc_prod_type_date_i
          const p = [loc];
          if(prod) p.push(prod);
          p.push(tr.value, fDate, i);
          sampleCode = p.join('_');
        } else if(tr.value === 'TR') {
          // UHG-Geo/BN-Geo TR: UHGTR0446_001 формат
          const abbr = unitAbbreviations[cVal] || '';
          const idx = String(i).padStart(3, '0');
          sampleCode = `${abbr}TR${loc}_${idx}`;
        } else if(tr.value === 'Stock') {
          // UHG-Geo/BN-Geo Stock: UHG_S6A_20251202_1 формат
          const abbr = unitAbbreviations[cVal] || '';
          sampleCode = `${abbr}_S${loc}_${fDate}_${i}`;
        } else {
          // UHG-Geo/BN-Geo бусад (GRD, TE, PE, CQ): UHG_GRD_0446_20251202_1 формат
          const abbr = unitAbbreviations[cVal] || '';
          sampleCode = `${abbr}_${tr.value}_${loc}_${fDate}_${i}`;
        }
        samples.push(sampleCode);
      }
    } else {
      entryContainer.innerHTML = `
        <div class="sample-list-empty">
          <i class="bi bi-info-circle"></i>
          <h4>No auto-generator available</h4>
          <p>Will be registered directly</p>
        </div>
      `;
      return;
    }

    if (samples.length === 0) {
      entryContainer.innerHTML = `
        <div class="sample-list-empty">
          <i class="bi bi-exclamation-circle" style="color: #ef4444;"></i>
          <h4>No samples found</h4>
          <p>Please check the settings</p>
        </div>
      `;
      return;
    }

    // Update badge
    if(sampleCountBadge) sampleCountBadge.textContent = `${samples.length} sample(s)`;

    let html = '';

    // ============ CHPP: Column Groups ============
    if (isChpp && Object.keys(groupedSamples).length > 0) {
      let inputIndex = 0;
      const groupOrder = ['CC', 'TC', 'MOD I', 'MOD II', 'MOD III', 'PF', 'Constant'];

      const iconMap = {
        'CC': 'bi-circle-fill',
        'TC': 'bi-circle',
        'MOD I': 'bi-1-circle-fill',
        'MOD II': 'bi-2-circle-fill',
        'MOD III': 'bi-3-circle-fill',
        'PF': 'bi-box-fill',
        'Constant': 'bi-pin-fill'
      };

      html = '<div class="chpp-columns">';

      groupOrder.forEach((groupName, groupIdx) => {
        if (!groupedSamples[groupName]) return;
        const items = groupedSamples[groupName];
        const groupId = `grp-${groupIdx}`;

        html += `
          <div class="module-column" data-group="${escapeAttr(groupId)}">
            <div class="module-column-header" data-toggle-group="${escapeAttr(groupId)}">
              <i class="bi ${iconMap[groupName] || 'bi-folder'}"></i>
              <span>${escapeAttr(groupName)}</span>
              <span class="col-count">${items.length}</span>
              <input type="checkbox" class="col-check" id="chk-${escapeAttr(groupId)}" checked data-toggle-group="${escapeAttr(groupId)}">
            </div>
            <div class="module-column-items">
        `;

        items.forEach(item => {
          const name = typeof item === 'string' ? item : item.name;
          const label = typeof item === 'string' ? item : item.label;
          const displayLabel = label.split('_')[0];

          if (listType === 'chpp_12h') {
            html += `
              <div class="col-item">
                <input type="checkbox" name="sample_codes" value="${escapeAttr(name)}" class="col-item-check grp-${escapeAttr(groupId)}" checked>
                <span class="col-item-code" title="${escapeAttr(label)}">${escapeAttr(displayLabel)}</span>
              </div>
            `;
          } else {
            html += `
              <div class="col-item">
                <input type="hidden" name="sample_codes" value="${escapeAttr(name)}">
                <span class="col-item-code" title="${escapeAttr(label)}">${escapeAttr(displayLabel)}</span>
                ${requiresWeight ? `
                  <div class="col-item-weight">
                    <input type="text" inputmode="numeric" pattern="[0-9]*" name="weights" class="weight-input" data-index="${inputIndex}" autocomplete="off">
                  </div>
                ` : ''}
              </div>
            `;
            inputIndex++;
          }
        });

        html += `</div></div>`;
      });

      html += '</div>';
      if(listType) html += `<input type="hidden" name="list_type" value="${listType}">`;

    } else {
      // ============ Non-CHPP: Regular Table ============
      html = `
      <table class="sample-table" id="sample-list-table">
        <thead>
          <tr>
            <th class="row-num">#</th>
            <th>Code</th>
            <th>Analysis</th>
            ${requiresWeight ? '<th style="width:60px;">Weight</th>' : ''}
          </tr>
        </thead>
        <tbody>`;

      samples.forEach((name, idx) => {
        html += `
        <tr>
          <td class="row-num">${idx+1}</td>
          <td>
            <input type="text" name="sample_codes" value="${escapeAttr(name)}" class="sample-code-input" autocomplete="off">
          </td>
          <td class="analysis-badges"></td>
          ${requiresWeight ? `<td><input type="text" inputmode="numeric" pattern="[0-9]*" name="weights" class="weight-input" data-index="${idx}" autocomplete="off"></td>` : ''}
        </tr>`;
      });

      html += `</tbody></table>`;
      if(listType) html += `<input type="hidden" name="list_type" value="${listType}">`;
    }

    entryContainer.innerHTML = html;

    // Setup weight input arrow navigation
    setupWeightNavigation();

    // Fetch analyses preview (only for non-CHPP)
    if (!isChpp && samples.length > 0) {
      fetchAnalysesPreview(samples);
    }
  }

  // Arrow key navigation for weight inputs
  function setupWeightNavigation() {
    const weightInputs = document.querySelectorAll('.weight-input');

    weightInputs.forEach((input, idx) => {
      input.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowDown' || e.key === 'Enter') {
          e.preventDefault();
          const nextInput = weightInputs[idx + 1];
          if (nextInput) {
            nextInput.focus();
            nextInput.select();
          }
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          const prevInput = weightInputs[idx - 1];
          if (prevInput) {
            prevInput.focus();
            prevInput.select();
          }
        }
      });

      // Auto-select on focus
      input.addEventListener('focus', function() {
        this.select();
      });
    });

    // Focus first weight input
    if (weightInputs.length > 0) {
      setTimeout(() => weightInputs[0].focus(), 100);
    }
  }

  // Alert helper
  function showAlert(msg) {
    alert(msg);
  }

  // ------------------------ 7. PREVIEW FUNCTION ------------------------
  async function fetchAnalysesPreview(sampleNames) {
    const c = document.querySelector('input[name="client_name"]:checked');
    const t = document.querySelector('#sample-type-container input:checked');
    if (!c || !t) return;

    const rows = document.querySelectorAll('#sample-list-table tbody tr');
    const map = new Map();
    rows.forEach(r => {
      const inp = r.querySelector('input[name="sample_codes"]');
      const val = inp ? inp.value : null;
      const cell = r.querySelector('.analysis-badges');
      if (val && cell) {
        map.set(val, cell);
        cell.innerHTML = '<span style="color:#94a3b8;font-size:0.65rem;">...</span>';
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
            return `<span class="analysis-badge" title="${displayNameWithAlias(b)}">${displayCodeAlias(b)}</span>`;
          }).join('');
          cell.innerHTML = badges;
        } else if (cell) {
          cell.innerHTML = '<span style="color:#94a3b8;font-size:0.65rem;">-</span>';
        }
      }
    } catch (e) { logger.error(e); }
  }

  // ------------------------ 8. TOGGLE COLUMN GROUP ------------------------
  function toggleColumnGroup(groupId) {
    const headerCheck = document.getElementById(`chk-${groupId}`);
    const itemChecks = document.querySelectorAll(`.grp-${groupId}`);

    if (headerCheck && itemChecks.length > 0) {
      // Toggle: if all checked -> uncheck all, else check all
      const allChecked = Array.from(itemChecks).every(cb => cb.checked);
      const newState = !allChecked;

      headerCheck.checked = newState;
      itemChecks.forEach(cb => cb.checked = newState);
    }
  }

  // Event delegation — inline onclick-ийн оронд
  entryContainer.addEventListener('click', function(e) {
    const toggler = e.target.closest('[data-toggle-group]');
    if (toggler) {
      e.stopPropagation();
      toggleColumnGroup(toggler.dataset.toggleGroup);
    }
  });

  // Update header checkbox when individual items change
  function setupColumnGroupListeners() {
    document.querySelectorAll('.col-item-check').forEach(cb => {
      cb.addEventListener('change', function() {
        const classes = this.className.split(' ');
        const grpClass = classes.find(c => c.startsWith('grp-'));
        if (!grpClass) return;

        const groupId = grpClass.replace('grp-', '');
        const headerCheck = document.getElementById(`chk-${groupId}`);
        const itemChecks = document.querySelectorAll(`.${grpClass}`);

        if (headerCheck) {
          const allChecked = Array.from(itemChecks).every(c => c.checked);
          headerCheck.checked = allChecked;
        }
      });
    });
  }

  // ------------------------ 9. EVENTS ------------------------
  document.querySelectorAll('.generate-btn').forEach(btn => btn.addEventListener('click', function() {
    generateSampleList();
    // Setup listeners after generation
    setTimeout(setupColumnGroupListeners, 50);
  }));

  if(twohPrimarySelect) { twohPrimarySelect.addEventListener('change', refresh2hSecondaryOptions); }
  if(comPrimarySelect) { comPrimarySelect.addEventListener('change', refreshComSecondaryOptions); }

  // MG: set sample_code from preview before form submit
  const sampleForm = document.getElementById('sample-form');
  if (sampleForm) {
    sampleForm.addEventListener('submit', function() {
      const cRadio = document.querySelector('input[name="client_name"]:checked');
      const tRadio = document.querySelector('#sample-type-container input:checked');
      if (cRadio && cRadio.value === 'WTL' && tRadio && tRadio.value === 'MG') {
        const preview = document.getElementById('wtl_mg_preview');
        const sc = document.getElementById('sample_code');
        if (preview && sc) sc.value = preview.value;
      }
    });
  }

});
