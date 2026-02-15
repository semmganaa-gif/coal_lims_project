$(function () {
  // Шинжилгээний хуудасны үндсэн скрипт (v10 - Auto Badge)

  const analysisCodeRaw     = window.LIMS_ANALYSIS_CODE_RAW;
  const analysisCodeDisplay = window.LIMS_ANALYSIS_CODE_DISPLAY;
  const rejected   = window.REJECTED_SAMPLES || {};
  const existing   = window.EXISTING_RESULTS || {};
  const errLabels  = window.ERROR_LABELS || {};

  // ===== SAMPLE IDs СЭРГЭЭХ & СИНКЛЭХ (localStorage) =====
  (function restoreSampleIds() {
    if (!analysisCodeRaw) return;

    const url = new URL(window.location.href);
    const urlSampleIds = url.searchParams.get('sample_ids');
    const storageKey = `worksheet_${analysisCodeRaw}_sample_ids`;

    try {
      if (urlSampleIds) {
        // URL-д sample_ids байвал localStorage-д синк хийх
        localStorage.setItem(storageKey, urlSampleIds);
      } else {
        // URL-д байхгүй бол localStorage-ээс сэргээх
        const savedIds = localStorage.getItem(storageKey);
        if (savedIds && savedIds.trim()) {
          url.searchParams.set('sample_ids', savedIds);
          window.location.href = url.toString();
          return;
        }
      }
    } catch(e) {
      console.warn('localStorage sync алдаа:', e);
    }
  })();

  // ------- Туслах функцүүд -------
  function setIf(val, sel){ if(val!==undefined && sel){ const $el=$(sel); if($el.length) $el.val(val) } }
  function restoreParallel(rawPar, sampleId, p){
    if(!rawPar) return;
    setIf(rawPar.num,         `#sample_${sampleId}_${p}_num`);
    setIf(rawPar.dish_num,    `#sample_${sampleId}_${p}_dish_num`);
    setIf(rawPar.bottle_num,  `#sample_${sampleId}_${p}_bottle_num`);
    setIf(rawPar.bottle,      `#sample_${sampleId}_${p}_bottle`);
    setIf(rawPar.m1,          `#sample_${sampleId}_${p}_m1`);
    setIf(rawPar.m2_sample,   `#sample_${sampleId}_${p}_m2`);
    setIf(rawPar.m2,          `#sample_${sampleId}_${p}_m2`);
    setIf(rawPar.m3_ashy,     `#sample_${sampleId}_${p}_m3_ashy`);
    setIf(rawPar.m3_dish_dry, `#sample_${sampleId}_${p}_m3_dish_dry`);
    setIf(rawPar.m3_residue,  `#sample_${sampleId}_${p}_m3_residue`);
  }
  function setBusy(busy) {
    const $btn = $('#save-analysis-results');
    if (busy) $btn.prop('disabled', true).html('<i class="bi bi-arrow-repeat"></i> ...');
    else      $btn.prop('disabled', false).html('<i class="bi bi-check-lg"></i> Save Results');
  }
  function selectableInputs(scope){
    return $(scope).find('.form-input,[data-lims-input],input[type="number"],input[type="text"]').filter(function(){
      return !this.readOnly && !this.disabled;
    });
  }
  function pushRowDataFlex(payloadArr, rowData){
    if (!rowData) return;
    if (Array.isArray(rowData)) payloadArr.push(...rowData);
    else payloadArr.push(rowData);
  }

  function clearSampleIdsStorage(analysisCode){
    try {
      const storageKey = `worksheet_${analysisCode}_sample_ids`;
      localStorage.removeItem(storageKey);
      const url = new URL(window.location.href);
      url.searchParams.delete('sample_ids');
      window.history.replaceState({}, '', url.toString());
    } catch(e){}
  }

  function lockRowsAndClearStorage(payload, analysisCode, tableId) {
    const $tbl = $(tableId);
    if (!$tbl.length) return;
    payload.forEach(p => {
      const sid = String(p.sample_id);
      const $rows = $tbl.find(`tr[data-sample-id="${sid}"]`);
      if (!$rows.length) return;
      selectableInputs($rows).each(function () {
        this.readOnly = true;
        this.classList.add('bg-light');
        const id = this.id;
        try{
            ['analysis_',''].forEach(prefix => {
                const k = `${prefix}${analysisCodeRaw}_${id}`;
                localStorage.removeItem(k); localStorage.setItem(k+'_locked','true');
                sessionStorage.removeItem(k); sessionStorage.setItem(k+'_locked','true');
            });
        }catch(e){}
      });
    });
  }

  function postPayload(payload, callback, analysisCode, tableId) {
    let timedOut = false;
    const t = setTimeout(() => {
      timedOut = true; setBusy(false);
      alert('Server did not respond. Please try again.');
    }, 12000);

    // Get CSRF token from meta tag
    const csrfToken = $('meta[name="csrf-token"]').attr('content');

    $.ajax({
      url: "/api/save_results",
      method: "POST",
      contentType: "application/json; charset=utf-8",
      headers: {
        'X-CSRFToken': csrfToken
      },
      data: JSON.stringify(payload),
      timeout: 11000
    })
    .done(function(resp) {
      if (timedOut) return;

      const savedPayload = resp.results || payload;
      const failedItems = resp.errors || [];

      // ✅ Алдаатай дээжүүдийг консолд харуулах
      if (failedItems.length > 0) {
        console.warn(`⚠️ ${failedItems.length} дээж хадгалагдсангүй:`);
        failedItems.forEach(err => {
          console.warn(`   - Sample ${err.sample_id}: ${err.error}`);
        });
      }

      lockRowsAndClearStorage(savedPayload, analysisCode, tableId);
      clearSampleIdsStorage(analysisCodeRaw);

      // AG Grid: afterSave callback шалгах (reload хийхгүй)
      const afterSaveCallback = window.LIMS_CALC?.[analysisCode]?.afterSave;
      const useAfterSave = typeof afterSaveCallback === 'function';

      // ✅ Check statuses and show appropriate message
      if (savedPayload && savedPayload.length > 0) {
        const statuses = savedPayload.map(r => r.status).filter(s => s);
        const hasPendingReview = statuses.some(s => s === 'pending_review');
        const allApproved = statuses.every(s => s === 'approved');

        if (hasPendingReview) {
          // Has tolerance issue → inform but stay on page
          alert(resp?.message || 'Saved. Tolerance exceeded, senior review required.');
          if (callback) callback(resp);
          // AG Grid: afterSave дуудах, эсвэл reload
          if (useAfterSave) {
            afterSaveCallback(savedPayload, failedItems);
          } else {
            setTimeout(function() { window.location.reload(); }, 500);
          }
          return;
        } else if (allApproved) {
          // All approved → inform and stay on page
          alert(resp?.message || 'Saved. All automatically approved.');
          if (callback) callback(resp);
          // AG Grid: afterSave дуудах, эсвэл reload
          if (useAfterSave) {
            afterSaveCallback(savedPayload, failedItems);
          } else {
            setTimeout(function() { window.location.reload(); }, 500);
          }
          return;
        }
      }

      // Default: just show message and reload or call afterSave
      alert(resp?.message || 'Saved');
      if (callback) callback(resp);
      if (useAfterSave) {
        afterSaveCallback(savedPayload, failedItems);
      } else {
        setTimeout(function() { window.location.reload(); }, 500);
      }
    })
    .fail(function(xhr) {
      if (timedOut) return;
      alert(xhr?.responseJSON?.message || 'Error saving data.');
    })
    .always(function() {
      if (timedOut) return;
      clearTimeout(t);
      setBusy(false);
    });
  }

  // ===========================================================
  // ✅ RESTORE LOGIC + AUTO BADGE INJECTION
  // ===========================================================
  const $allTables = $('table[id$="-analysis-table"]');

  Object.keys(rejected).forEach(sidStr => {
    const sid = parseInt(sidStr, 10);
    const $rows = $allTables.find(`tbody tr[data-sample-id="${sid}"]`);

    // 1. Input-уудыг нээх (Unlock)
    selectableInputs($rows).each(function(){
      $(this).prop('readonly', false).prop('disabled', false).removeClass('bg-light');
    });

    // 2. Өмнөх утгуудыг сэргээх
    const rec = existing[sid];
    if(analysisCodeRaw !== 'Gi' && analysisCodeRaw !== 'CSN' && rec && rec.raw_data){
      let raw = rec.raw_data; try{ if(typeof raw==='string') raw = JSON.parse(raw) }catch(e){ raw = {} }
      restoreParallel(raw.p1, sid, 'p1'); restoreParallel(raw.p2, sid, 'p2');
    }
    if(typeof window.calculateAndDisplayForRow === 'function' && analysisCodeRaw !== 'TRD'){
        window.calculateAndDisplayForRow(sid, false);
    }

    // 3. ✅ Алдааны мэдээллийг дээжний нэрний доор харуулах
    const info = rejected[sidStr];
    if(info) {
        const rCode = info.reason_code;
        // Монгол тайлбарыг олох, олдохгүй бол legacy reason, эсвэл default
        const reasonText = errLabels[rCode] || info.reason || "Rejected";

        const badgeHtml = `
            <div class="mt-1">
                <span class="badge bg-danger text-wrap text-start border border-light"
                      style="font-size:0.7rem; line-height:1.2; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                    <i class="bi bi-exclamation-triangle-fill me-1"></i> ${reasonText}
                </span>
            </div>
        `;

        // Хүснэгтийн 2-р багана (Index 1) нь ихэвчлэн Дээжний Нэр байдаг
        const $nameCell = $rows.find('td').eq(1);
        if($nameCell.length) {
            // Давхардахаас сэргийлэх
            if($nameCell.find('.badge.bg-danger').length === 0) {
                $nameCell.append(badgeHtml);
            }
        }
    }
  });

  // FM Fallback
  if (analysisCodeRaw === 'FM' && typeof window.calculateAndDisplayForRow !== 'function') {
    (function(){
      const TABLE_SEL = '#free-moisture-analysis-table';
      window.calculateAndDisplayForRow = function(sampleId, lock){ return null; };
    })();
  }

  // ===== MODAL =====
  let modalSelectedOrder = new Set();

  $('#selectSamplesModal').on('show.bs.modal', function(){
    modalSelectedOrder = new Set();
    const modal = $(this), body = modal.find('.modal-body');
    body.html('<p class="text-center">Loading...</p>');

    console.log('[Modal] Loading eligible samples for:', analysisCodeRaw);

    $.getJSON(`/api/eligible_samples/${analysisCodeRaw}`)
    .done(function(resp){
      console.log('[Modal] API response:', resp);
      const samples = resp.samples || [];
      const rejected = resp.rejected || [];
      const rejectedCount = resp.rejected_count || 0;
      const canUnassign = window.userRole === 'senior' || window.userRole === 'admin';

      // Tab-тай modal бүтэц
      let html = `
        <ul class="nav nav-tabs mb-3" role="tablist">
          <li class="nav-item" role="presentation">
            <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#newSamplesTab" type="button">
              <i class="bi bi-plus-circle me-1"></i>New Samples
              <span class="badge bg-primary ms-1">${samples.length}</span>
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link ${rejectedCount > 0 ? 'text-danger' : ''}" data-bs-toggle="tab" data-bs-target="#rejectedSamplesTab" type="button">
              <i class="bi bi-exclamation-triangle me-1"></i>Retest
              ${rejectedCount > 0 ? '<span class="badge bg-danger ms-1">' + rejectedCount + '</span>' : '<span class="badge bg-secondary ms-1">0</span>'}
            </button>
          </li>
        </ul>
        <div class="tab-content">`;

      // --- Шинэ дээж tab ---
      html += `<div class="tab-pane fade show active" id="newSamplesTab">`;
      if(!samples.length){
        html += `<p class="text-center text-muted py-4">No new samples assigned to this analysis.</p>`;
      } else {
        // Unique values for dropdowns
        const uniqueClients = [...new Set(samples.map(s => s.client_name).filter(Boolean))].sort();
        const uniqueTypes = [...new Set(samples.map(s => s.sample_type).filter(Boolean))].sort();

        html += `
          <div class="row g-2 mb-2">
            <div class="col-5">
              <input type="text" id="filter-sample-code" class="form-control form-control-sm" placeholder="Search sample code...">
            </div>
            <div class="col-4">
              <select id="filter-client" class="form-select form-select-sm">
                <option value="">All Clients</option>
                ${uniqueClients.map(c => `<option value="${c}">${c}</option>`).join('')}
              </select>
            </div>
            <div class="col-3">
              <select id="filter-type" class="form-select form-select-sm">
                <option value="">All Types</option>
                ${uniqueTypes.map(t => `<option value="${t}">${t}</option>`).join('')}
              </select>
            </div>
          </div>
          <div class="d-flex justify-content-between align-items-center mb-2">
            <small class="text-muted"><span id="filtered-count">${samples.length}</span> / ${samples.length} samples</small>
            <button type="button" class="btn btn-link btn-sm p-0" id="clear-filters">Clear</button>
          </div>
          <div class="table-responsive" style="max-height: 320px; overflow-y: auto;">
            <table class="table table-sm table-hover mb-0" id="selectable-samples-table">
              <thead class="table-light sticky-top">
                <tr>
                  <th style="width:40px"><input type="checkbox" id="select-all-modal-samples"></th>
                  <th>Sample Code</th>
                  <th>Client</th>
                  <th>Type</th>
                  ${canUnassign ? '<th style="width:50px">Remove</th>' : ''}
                </tr>
              </thead>
              <tbody>`;
        samples.forEach(s=>{
          html += `<tr data-code="${(s.sample_code||'').toLowerCase()}" data-client="${(s.client_name||'').toLowerCase()}" data-type="${(s.sample_type||'').toLowerCase()}" data-sample-id="${s.id}">
            <td><input type="checkbox" class="modal-sample-checkbox" value="${s.id}"></td>
            <td>${s.sample_code}</td>
            <td>${s.client_name||'-'}</td>
            <td>${s.sample_type||'-'}</td>
            ${canUnassign ? `<td><button type="button" class="btn btn-outline-danger btn-sm btn-unassign-sample" data-id="${s.id}" data-code="${s.sample_code}" title="Remove from analysis"><i class="bi bi-x-lg"></i></button></td>` : ''}
          </tr>`;
        });
        html += `</tbody></table></div>`;
      }
      html += `</div>`;

      // --- Давтах дээж tab ---
      html += `<div class="tab-pane fade" id="rejectedSamplesTab">`;
      if(!rejected.length){
        html += `<p class="text-center text-muted py-4">No samples requiring retest.</p>`;
      } else {
        html += `
          <div class="alert alert-warning py-2 mb-2">
            <i class="bi bi-info-circle me-1"></i>
            These samples were rejected during senior review. Reanalysis is required.
          </div>
          <div class="mb-2">
            <input type="text" id="filter-rejected-code" class="form-control form-control-sm" placeholder="Search sample code...">
          </div>
          <div class="table-responsive" style="max-height: 320px; overflow-y: auto;">
            <table class="table table-sm table-hover mb-0" id="rejected-samples-table">
              <thead class="table-light sticky-top">
                <tr>
                  <th style="width:40px"><input type="checkbox" id="select-all-rejected-samples"></th>
                  <th>Sample Code</th>
                  <th>Client</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>`;
        rejected.forEach(s=>{
          const errLabel = errLabels[s.error_reason] || s.error_reason || '-';
          html += `<tr data-code="${(s.sample_code||'').toLowerCase()}">
            <td><input type="checkbox" class="modal-sample-checkbox rejected-sample" value="${s.id}"></td>
            <td>${s.sample_code}</td>
            <td>${s.client_name||'-'}</td>
            <td><span class="badge bg-danger">${errLabel}</span></td>
          </tr>`;
        });
        html += `</tbody></table></div>`;
      }
      html += `</div>`;

      html += `</div>`; // tab-content end
      body.html(html);

      // Select all - шинэ дээж
      body.find('#select-all-modal-samples').on('change', function(){
        const checked = this.checked;
        body.find('#selectable-samples-table .modal-sample-checkbox:visible').each(function(){
          $(this).prop('checked', checked).trigger('change');
        });
      });

      // Select all - rejected дээж
      body.find('#select-all-rejected-samples').on('change', function(){
        const checked = this.checked;
        body.find('#rejected-samples-table .modal-sample-checkbox:visible').each(function(){
          $(this).prop('checked', checked).trigger('change');
        });
      });
    });
  });

  // Advanced filter function
  function applyFilters() {
    const codeFilter = ($('#filter-sample-code').val() || '').toLowerCase().trim();
    const clientFilter = ($('#filter-client').val() || '').toLowerCase();
    const typeFilter = ($('#filter-type').val() || '').toLowerCase();

    let visibleCount = 0;
    $('#selectable-samples-table tbody tr').each(function() {
      const $row = $(this);
      const code = $row.data('code') || '';
      const client = $row.data('client') || '';
      const type = $row.data('type') || '';

      const matchCode = !codeFilter || code.includes(codeFilter);
      const matchClient = !clientFilter || client === clientFilter;
      const matchType = !typeFilter || type === typeFilter;

      if (matchCode && matchClient && matchType) {
        $row.show();
        visibleCount++;
      } else {
        $row.hide();
      }
    });

    $('#filtered-count').text(visibleCount);
  }

  // Filter events
  $(document).on('input', '#filter-sample-code', applyFilters);
  $(document).on('change', '#filter-client', applyFilters);
  $(document).on('change', '#filter-type', applyFilters);

  // Clear filters
  $(document).on('click', '#clear-filters', function() {
    $('#filter-sample-code').val('');
    $('#filter-client').val('');
    $('#filter-type').val('');
    applyFilters();
  });

  // Rejected tab filter function
  function applyRejectedFilters() {
    const codeFilter = ($('#filter-rejected-code').val() || '').toLowerCase().trim();

    let visibleCount = 0;
    $('#rejected-samples-table tbody tr').each(function() {
      const $row = $(this);
      const code = $row.data('code') || '';

      if (!codeFilter || code.includes(codeFilter)) {
        $row.show();
        visibleCount++;
      } else {
        $row.hide();
      }
    });
  }

  // Rejected tab filter event
  $(document).on('input', '#filter-rejected-code', applyRejectedFilters);

  // Legacy filter (for backwards compatibility)
  $(document).on('keyup', '#modal-sample-filter', function() {
    const value = $(this).val().toLowerCase();
    $("#selectable-samples-table tbody tr").filter(function() {
      $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    });
  });

  $(document).on('change','.modal-sample-checkbox', function(){
    const id = $(this).val();
    if(this.checked) modalSelectedOrder.add(id); else modalSelectedOrder.delete(id);
  });

  // Row click to toggle checkbox
  $(document).on('click', '#selectSamplesModal tbody tr', function(e) {
    if ($(e.target).is('input[type="checkbox"]') || $(e.target).closest('.btn-unassign-sample').length) return;
    const $checkbox = $(this).find('.modal-sample-checkbox');
    if ($checkbox.length) {
      $checkbox.prop('checked', !$checkbox.prop('checked')).trigger('change');
    }
  });

  // Дээжийг шинжилгээнээс хасах (senior/admin only)
  $(document).on('click', '.btn-unassign-sample', function(e) {
    e.stopPropagation();
    const $btn = $(this);
    const sampleId = $btn.data('id');
    const sampleCode = $btn.data('code');

    if (!confirm(`Remove sample "${sampleCode}" from ${analysisCodeRaw} analysis?`)) {
      return;
    }

    $btn.prop('disabled', true).html('<i class="bi bi-hourglass-split"></i>');

    $.ajax({
      url: '/api/unassign_sample',
      method: 'POST',
      contentType: 'application/json',
      headers: { 'X-CSRFToken': window.csrfToken },
      data: JSON.stringify({
        sample_id: sampleId,
        analysis_code: analysisCodeRaw
      }),
      success: function(resp) {
        if (resp.success) {
          $btn.closest('tr').fadeOut(300, function() { $(this).remove(); });
          // Update count
          const $count = $('#filtered-count');
          if ($count.length) {
            const newCount = parseInt($count.text()) - 1;
            $count.text(newCount);
          }
        } else {
          alert(resp.message || 'An error occurred');
          $btn.prop('disabled', false).html('<i class="bi bi-x-lg"></i>');
        }
      },
      error: function(xhr) {
        const msg = xhr.responseJSON?.message || 'Server connection error';
        alert(msg);
        $btn.prop('disabled', false).html('<i class="bi bi-x-lg"></i>');
      }
    });
  });

  $('#add-selected-samples-to-worksheet').on('click', function(){
    if(!modalSelectedOrder.size){ alert("Please select samples."); return; }
    const url = new URL(window.location.href);
    const exist = url.searchParams.get('sample_ids') ? url.searchParams.get('sample_ids').split(',') : [];
    const reallyNew = [...modalSelectedOrder].filter(x=>!exist.includes(x));
    const allIds = [...exist, ...reallyNew];

    // ✅ localStorage-д хадгалах (буцаж ирэхэд сэргээхийн тулд)
    const storageKey = `worksheet_${analysisCodeRaw}_sample_ids`;
    try {
      localStorage.setItem(storageKey, allIds.join(','));
    } catch(e) {
      console.warn('localStorage хадгалах алдаа:', e);
    }

    url.searchParams.set('sample_ids', allIds.join(','));
    window.location.href = url.toString();
  });

  // ===== SAVE =====
  const TABLE_BY_CODE = {
    'Aad':'#ash-analysis-table',
    'Mad':'#madGrid','Vad':'#madGrid','MT':'#mtGrid',
    'TS':'#sulfurGrid','St,ad':'#sulfurGrid',
    'CV':'#cvGrid','Qgr,ad':'#cvGrid',
    'Gi':'#GiGrid','CSN':'#csnGrid',
    'FM':'#fmGrid',
    'Cl':'#chlorine-analysis-table','Cl,ad':'#chlorine-analysis-table',
    'F':'#fluorine-analysis-table','F,ad':'#fluorine-analysis-table',
    'P':'#phosphorus-analysis-table','P,ad':'#phosphorus-analysis-table',
    'TRD':'#trdGrid',
    'SOLID':'#solidGrid','Solid':'#solidGrid','solid':'#solidGrid',
    'X':'#xyGrid','Y':'#xyGrid',
    'CRI':'#cricSrGrid','CSR':'#cricSrGrid',
  };
  const SINGLE_VALUE_CODES = new Set(['FM','SOLID','X','Y','CRI','CSR']);
  function collectSingleRowPayload($row){
    const sid = parseInt($row.data('sample-id'), 10); if(!sid) return null;
    let $inp = $row.find(`#sample_${sid}_p1_result`);
    if(!$inp.length) $inp = $row.find(`#sample_${sid}_result`);
    if(!$inp.length) $inp = $row.find('input[name*="result"]');
    if(!$inp.length) return null;
    const valStr = ($inp.val() ?? '').toString().trim(); if(valStr==='') return null;
    const valNum = Number(valStr); if(Number.isNaN(valNum)) return null;
    return { sample_id:sid, analysis_code:analysisCodeRaw, final_result:valNum, raw_data:{ p1:{ result:valNum, _single:true } } };
  }

  $('#save-analysis-results').off('click.save').on('click.save', function(){
    setBusy(true);
    let payload = [];
    const tableId = TABLE_BY_CODE[analysisCodeRaw] || TABLE_BY_CODE[analysisCodeDisplay];
    if (!tableId) { setBusy(false); alert('Matching table not found'); return; }
    const $tbl = $(tableId);

    // 1) AG Grid collector (аль alias-ээр бүртгэгдсэн ч бай)
    const collector =
      window.LIMS_CALC?.[analysisCodeRaw]?.collect ||
      window.LIMS_CALC?.[analysisCodeRaw?.toUpperCase()]?.collect ||
      window.LIMS_CALC?.[analysisCodeRaw?.toLowerCase()]?.collect ||
      window.LIMS_CALC?.[analysisCodeDisplay]?.collect;
    if (typeof collector === 'function') {
        payload = collector();
    }
    // 2) Хуучин table хэлбэрийн calc функц (p1/p2)
    else if (typeof window.calculateAndDisplayForRow === 'function') {
        const sampleIds = new Set();
        $tbl.find('tbody tr[data-sample-id]').each(function(){
            const p = $(this).data('parallel');
            if (p === 1 || p === undefined) sampleIds.add($(this).data('sample-id'));
        });
        sampleIds.forEach((sid) => {
            try{
                if (analysisCodeRaw !== 'TRD') {
                    const rowData = window.calculateAndDisplayForRow(sid, true);
                    pushRowDataFlex(payload, rowData);
                }
            }catch(e){ console.warn('calc error for sid=', sid, e); }
        });
    }
    // 3) Нэг мөрийн шинжилгээ
    else if (SINGLE_VALUE_CODES.has(analysisCodeRaw)) {
        $tbl.find('tbody tr[data-sample-id]').each(function(){
            const p = $(this).data('parallel'); if (p && Number(p)!==1) return;
            const one = collectSingleRowPayload($(this)); if (one) payload.push(one);
        });
    }

    if (!payload.length) { setBusy(false); return alert('No new results to save.'); }
    postPayload(payload, null, analysisCodeRaw, tableId);
  });

  // Remove & Nav
  $(document).on('click','.remove-sample-from-worksheet', function(e){
    e.preventDefault();
    if(!confirm("Remove this sample?")) return;
    const sid = $(this).data('sample-id').toString();
    const url = new URL(window.location.href);
    let ids = url.searchParams.get('sample_ids') ? url.searchParams.get('sample_ids').split(',') : [];
    ids = ids.filter(x=>x!==sid);
    const storageKey=`worksheet_${analysisCodeRaw}_sample_ids`;
    localStorage.setItem(storageKey, ids.join(','));
    if(ids.length) url.searchParams.set('sample_ids', ids.join(',')); else url.searchParams.delete('sample_ids');
    window.location.href = url.toString();
  });

  (function installNavOnce(){
    if (window.__LIMS_NAV_INSTALLED__) return; window.__LIMS_NAV_INSTALLED__ = true;
    const ROW_SEL = 'table[id$="-analysis-table"] tbody tr[data-sample-id]';
    function rowInputs(row){ return Array.from(row.querySelectorAll('.form-input,[data-lims-input],input[type="number"],input[type="text"]')).filter(i => !i.readOnly && !i.disabled); }
    function nextInRow(inputs, el, dir){ const idx = inputs.indexOf(el); if (idx < 0) return inputs[0] || null; const n = inputs[idx + dir]; return n || (dir > 0 ? inputs[0] : inputs[inputs.length - 1]) || null; }
    document.addEventListener('keydown', function(ev){
      const k = ev.key;
      if (!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Enter'].includes(k)) return;
      const el = ev.target;
      if (!(el instanceof HTMLInputElement)) return;
      if (!el.closest('table[id$="-analysis-table"]')) return;
      const row = el.closest(ROW_SEL); if (!row) return;
      ev.preventDefault(); ev.stopPropagation();
      const inputs = rowInputs(row); let target = null;
      if (k==='ArrowLeft') target = nextInRow(inputs, el, -1);
      if (k==='ArrowRight' || k==='Enter') target = nextInRow(inputs, el, +1);
      if (k==='ArrowUp' || k==='ArrowDown'){
        const allRows = Array.from(document.querySelectorAll(ROW_SEL));
        const rowIdx  = allRows.indexOf(row);
        const row2    = allRows[rowIdx + (k==='ArrowDown' ? +1 : -1)];
        if (row2){
          const inputs2 = rowInputs(row2);
          const col     = Math.max(0, inputs.indexOf(el));
          if (inputs2.length) target = inputs2[Math.min(col, inputs2.length - 1)];
        }
      }
      if (target){ target.focus(); target.select?.(); }
    }, true);
  })();

  // Storage Sync
  const code = window.LIMS_ANALYSIS_CODE_RAW || window.LIMS_ANALYSIS_CODE_DISPLAY;
  document.querySelectorAll('table[id$="-analysis-table"] input').forEach(inp=>{
    try{ if(((inp.value??'')==='')){ const v = localStorage.getItem(`analysis_${code}_${inp.id}`); if(v!==null) inp.value = v; } }catch(e){}
  });
  document.addEventListener('input', (e)=>{
    const el=e.target; if(!(el instanceof HTMLInputElement) || !el.closest('table[id$="-analysis-table"]')) return;
    try{ localStorage.setItem(`analysis_${code}_${el.id}`, el.value ?? ''); }catch(e){}
  });
});
