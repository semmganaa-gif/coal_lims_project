/* equipment_modal.js — Equipment usage & calibration modal logic
   (extracted from analysis_page.html)
   Requires: window.EQ_I18N object for translated strings */

var _spareParts = null;

function loadSpareParts() {
  if (_spareParts) return Promise.resolve(_spareParts);
  return fetch('/spare_parts/api/list')
    .then(r => r.json())
    .then(data => { _spareParts = data; return data; });
}

function toggleRepairPanel(cb) {
  const panel = cb.closest('tr').querySelector('.repair-panel');
  if (cb.checked) {
    panel.classList.remove('d-none');
  } else {
    panel.classList.add('d-none');
  }
}

function addSparePart(btn) {
  const T = window.EQ_I18N || {};
  const list = btn.closest('.repair-panel').querySelector('.spare-parts-list');
  const row = document.createElement('div');
  row.className = 'input-group input-group-sm mb-1 spare-row';
  row.innerHTML = `
    <select class="form-select form-select-sm spare-select" style="flex:3">
      <option value="">${T.selectSparePart || 'Select spare part...'}</option>
    </select>
    <input type="number" class="form-control spare-qty" placeholder="${T.qty || 'Qty'}" min="1" value="1" style="flex:1; max-width:60px">
    <input type="text" class="form-control spare-user" placeholder="${T.who || 'Who'}" style="flex:2">
    <button type="button" class="btn btn-outline-danger btn-sm" onclick="this.closest('.spare-row').remove()">
      <i class="bi bi-x"></i>
    </button>
  `;
  list.appendChild(row);
  const sel = row.querySelector('.spare-select');
  loadSpareParts().then(parts => {
    parts.forEach(sp => {
      if (sp.quantity > 0) {
        const opt = document.createElement('option');
        opt.value = sp.id;
        opt.textContent = `${sp.name} (${sp.quantity} ${sp.unit || 'ш'})`;
        opt.dataset.quantity = sp.quantity;
        sel.appendChild(opt);
      }
    });
  });
}

// Calibration Panel Functions
function toggleCalibPanel(btn) {
  const T = window.EQ_I18N || {};
  const row = btn.closest('tr');
  const panel = row.querySelector('.calib-panel');
  if (panel) {
    panel.classList.toggle('d-none');
    btn.classList.toggle('btn-outline-success');
    btn.classList.toggle('btn-success');
    if (!panel.querySelector('.calib-freq')) {
      const title = panel.querySelector('.calib-panel-title');
      if (title) {
        const sel = document.createElement('select');
        sel.className = 'form-select form-select-sm calib-freq';
        sel.style.cssText = 'width:auto; margin-left:auto; font-size:0.68rem; padding:1px 24px 1px 6px; height:22px; border-radius:6px; -webkit-appearance:none; -moz-appearance:none; appearance:none; background-size:10px;';
        sel.innerHTML = '<option value="daily">' + (T.daily || 'Daily') + '</option><option value="monthly">' + (T.monthly || 'Monthly') + '</option><option value="adjustment">' + (T.adjustment || 'Adjustment') + '</option>';
        title.appendChild(sel);
      }
    }
  }
}

// Furnace Temperature Check
function checkTempDiff(input) {
  const row = input.closest('tr');
  const setTemp = parseFloat(row.querySelector('.calib-set-temp')?.value) || 0;
  const actualTemp = parseFloat(input.value) || 0;
  const diffInput = row.querySelector('.calib-temp-diff');
  const statusSpan = row.querySelector('.furnace-panel .calib-status');

  if (setTemp > 0 && actualTemp > 0) {
    const diff = actualTemp - setTemp;
    diffInput.value = (diff >= 0 ? '+' : '') + diff.toFixed(1) + ' °C';

    statusSpan.classList.remove('d-none');
    if (Math.abs(diff) <= 5) {
      statusSpan.textContent = 'OK';
      statusSpan.className = 'calib-status pass';
    } else {
      statusSpan.textContent = 'Diff!';
      statusSpan.className = 'calib-status fail';
    }
  } else {
    diffInput.value = '';
    statusSpan.classList.add('d-none');
  }
}

// Balance Weight Check
function checkWeightDiff(input) {
  const weightRow = input.closest('.calib-weight-row');
  const stdWt = parseFloat(weightRow.querySelector('.calib-std-wt')?.value) || 0;
  const measWt = parseFloat(input.value) || 0;
  const statusSpan = weightRow.querySelector('.calib-status');

  if (stdWt > 0 && measWt > 0) {
    const diff = Math.abs(measWt - stdWt);
    const tolerance = stdWt < 1 ? 0.0002 : 0.001;

    statusSpan.classList.remove('d-none');
    if (diff <= tolerance) {
      statusSpan.textContent = 'OK';
      statusSpan.className = 'calib-status pass';
    } else {
      statusSpan.textContent = '±' + diff.toFixed(4);
      statusSpan.className = 'calib-status fail';
    }
  } else {
    statusSpan.classList.add('d-none');
  }
}

function addWeightRow(btn) {
  const T = window.EQ_I18N || {};
  const list = btn.closest('.balance-panel').querySelector('.calib-weights-list');
  const row = document.createElement('div');
  row.className = 'calib-weight-row';
  row.innerHTML = `
    <input type="number" class="form-control form-control-sm calib-std-wt" placeholder="${T.stdG || 'Std (g)'}" step="0.0001" style="flex:1">
    <input type="number" class="form-control form-control-sm calib-meas-wt" placeholder="${T.measured || 'Measured'}" step="0.0001" style="flex:1" oninput="checkWeightDiff(this)">
    <span class="calib-status d-none" style="min-width:50px;"></span>
    <button type="button" class="btn btn-outline-secondary btn-sm" onclick="this.closest('.calib-weight-row').remove()" style="padding:2px 6px;">
      <i class="bi bi-x"></i>
    </button>
  `;
  list.appendChild(row);
}

// Ethanol pycnometer test
function calcEthanol(input) {
  const panel = input.closest('.balance-panel');
  const density = parseFloat(panel.querySelector('.ethanol-density')?.value) || 0;
  const volume = parseFloat(panel.querySelector('.ethanol-volume')?.value) || 0;
  const measured = parseFloat(panel.querySelector('.ethanol-measured')?.value) || 0;
  const expectedEl = panel.querySelector('.ethanol-expected');
  const diffEl = panel.querySelector('.ethanol-diff');
  const statusEl = panel.querySelector('.ethanol-status');

  if (density > 0 && volume > 0) {
    const expected = density * volume;
    expectedEl.value = expected.toFixed(4);

    if (measured > 0) {
      const diff = measured - expected;
      diffEl.value = (diff >= 0 ? '+' : '') + diff.toFixed(4);
      const tolerance = 0.001;
      statusEl.classList.remove('d-none');
      if (Math.abs(diff) <= tolerance) {
        statusEl.textContent = 'OK';
        statusEl.className = 'ethanol-status calib-status pass';
      } else {
        statusEl.textContent = 'FAIL';
        statusEl.className = 'ethanol-status calib-status fail';
      }
    } else {
      diffEl.value = '';
      statusEl.classList.add('d-none');
    }
  } else {
    expectedEl.value = '';
    diffEl.value = '';
    statusEl.classList.add('d-none');
  }
}

// CSN Temperature limits (MNS ISO 501)
const CSN_TEMP_TARGETS = {
  t1m30: {target: 800, tol: 10, min: 790, max: 810},
  t2m30: {target: 820, tol: 5,  min: 815, max: 825}
};

function checkCsnTemp(input) {
  const row = input.closest('.csn-crucible-row');
  const t2 = parseFloat(row.querySelector('.csn-temp-1m30')?.value);
  const t3 = parseFloat(row.querySelector('.csn-temp-2m30')?.value);
  const statusSpan = row.querySelector('.csn-row-status');

  const checks = [];
  if (!isNaN(t2)) checks.push(t2 >= CSN_TEMP_TARGETS.t1m30.min && t2 <= CSN_TEMP_TARGETS.t1m30.max);
  if (!isNaN(t3)) checks.push(t3 >= CSN_TEMP_TARGETS.t2m30.min && t3 <= CSN_TEMP_TARGETS.t2m30.max);

  if (checks.length === 0) {
    statusSpan.textContent = '—';
    statusSpan.style.color = '#94a3b8';
  } else if (checks.every(c => c)) {
    statusSpan.innerHTML = '<i class="bi bi-check-circle-fill"></i> OK';
    statusSpan.style.color = '#15803d';
  } else {
    statusSpan.innerHTML = '<i class="bi bi-x-circle-fill"></i> Fail';
    statusSpan.style.color = '#dc2626';
  }

  updateCsnFinalStatus(input.closest('.csn-panel'));
}

function updateCsnFinalStatus(panel) {
  const T = window.EQ_I18N || {};
  const rows = panel.querySelectorAll('.csn-crucible-row');
  const finalDiv = panel.querySelector('.csn-final-status');
  if (rows.length === 0) { finalDiv.classList.add('d-none'); return; }

  const lastRow = rows[rows.length - 1];
  const lastStatus = lastRow.querySelector('.csn-row-status');
  const isPass = lastStatus && lastStatus.textContent.includes('OK');
  const hasFail = lastStatus && lastStatus.textContent.includes('Fail');

  if (isPass) {
    finalDiv.classList.remove('d-none');
    finalDiv.style.background = '#dcfce7';
    finalDiv.style.color = '#15803d';
    finalDiv.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>' + (T.calibComplete || 'Calibration complete — ready for analysis');
  } else if (hasFail) {
    finalDiv.classList.remove('d-none');
    finalDiv.style.background = '#fef3c7';
    finalDiv.style.color = '#b45309';
    finalDiv.innerHTML = '<i class="bi bi-exclamation-triangle me-1"></i>' + (T.pleaseAdjustRetest || 'Please adjust and retest');
  } else {
    finalDiv.classList.add('d-none');
  }
}

function addCsnRetest(btn) {
  const T = window.EQ_I18N || {};
  const panel = btn.closest('.csn-panel');
  const list = panel.querySelector('.csn-crucible-list');
  const testNum = list.querySelectorAll('.csn-crucible-row').length + 1;

  const adjDiv = document.createElement('div');
  adjDiv.className = 'csn-adjust-row mb-1';
  adjDiv.style.cssText = 'display:flex; gap:4px; align-items:center; padding:4px 8px; background:#fefce8; border-radius:6px; border:1px dashed #fde047;';
  adjDiv.innerHTML = `
    <span style="font-size:0.65rem; color:#a16207; min-width:18px;"><i class="bi bi-wrench"></i></span>
    <div style="font-size:0.65rem; color:#a16207; font-weight:600; min-width:55px;">${T.adjustmentColon || 'Adjustment:'}</div>
    <div style="display:flex; gap:3px; align-items:center; flex:1;">
      <span style="font-size:0.6rem; color:#92400e;">${T.temp || 'Temp:'}</span>
      <input type="number" class="form-control form-control-sm csn-adj-temp" placeholder="°C" step="1" style="width:60px; font-size:0.75rem;">
    </div>
    <div style="display:flex; gap:3px; align-items:center; flex:1;">
      <span style="font-size:0.6rem; color:#92400e;">${T.current || 'Current:'}</span>
      <input type="number" class="form-control form-control-sm csn-adj-current" placeholder="sec" step="1" style="width:60px; font-size:0.75rem;">
    </div>
  `;
  list.appendChild(adjDiv);

  const row = document.createElement('div');
  row.className = 'csn-crucible-row mb-1';
  row.style.cssText = 'display:flex; gap:4px; align-items:center;';
  row.innerHTML = `
    <span style="font-size:0.7rem; min-width:18px; color:#1d4ed8;" title="${testNum}-р туршилт">T${testNum}</span>
    <input type="number" class="form-control form-control-sm csn-temp-1min" placeholder="°C" step="0.1" style="flex:1" oninput="checkCsnTemp(this)">
    <input type="number" class="form-control form-control-sm csn-temp-1m30" placeholder="°C" step="0.1" style="flex:1" oninput="checkCsnTemp(this)">
    <input type="number" class="form-control form-control-sm csn-temp-2m30" placeholder="°C" step="0.1" style="flex:1" oninput="checkCsnTemp(this)">
    <span class="csn-row-status" style="flex:0.7; font-size:0.7rem; font-weight:600; text-align:center;">—</span>
  `;
  list.appendChild(row);
}

// Drum Gi calibration
const DRUM_TARGETS = { '1min': 50, '5min': 250 };

function checkDrumRow(input) {
  const T = window.EQ_I18N || {};
  const panel = input.closest('.drum-panel');
  const meas1 = parseInt(panel.querySelector('.drum-meas-1min')?.value) || 0;
  const meas5 = parseInt(panel.querySelector('.drum-meas-5min')?.value) || 0;
  const st1 = panel.querySelector('.drum-status-1min');
  const st5 = panel.querySelector('.drum-status-5min');
  const finalEl = panel.querySelector('.drum-final-status');

  if (meas1 > 0) {
    if (meas1 === DRUM_TARGETS['1min']) {
      st1.innerHTML = '<span style="color:#15803d; font-weight:600;"><i class="bi bi-check-circle-fill"></i> OK</span>';
    } else {
      st1.innerHTML = '<span style="color:#dc2626; font-weight:600;"><i class="bi bi-x-circle-fill"></i> ' + meas1 + ' (≠50)</span>';
    }
  } else { st1.innerHTML = ''; }

  if (meas5 > 0) {
    if (meas5 === DRUM_TARGETS['5min']) {
      st5.innerHTML = '<span style="color:#15803d; font-weight:600;"><i class="bi bi-check-circle-fill"></i> OK</span>';
    } else {
      st5.innerHTML = '<span style="color:#dc2626; font-weight:600;"><i class="bi bi-x-circle-fill"></i> ' + meas5 + ' (≠250)</span>';
    }
  } else { st5.innerHTML = ''; }

  if (meas1 > 0 && meas5 > 0) {
    const allOk = (meas1 === 50 && meas5 === 250);
    if (allOk) {
      finalEl.innerHTML = '<span style="color:#15803d; background:#dcfce7; padding:4px 12px; border-radius:8px;"><i class="bi bi-check-circle-fill me-1"></i>' + (T.calibrationComplete || 'Calibration complete') + '</span>';
    } else {
      finalEl.innerHTML = '<span style="color:#b45309; background:#fef3c7; padding:4px 12px; border-radius:8px;"><i class="bi bi-exclamation-triangle-fill me-1"></i>' + (T.pleaseAdjust || 'Please adjust') + '</span>';
    }
  } else { finalEl.innerHTML = ''; }
}

// Drum prep calibration
function checkDrumDiff(input) {
  const panel = input.closest('.drum-panel');
  const before = parseInt(panel.querySelector('.drum-before')?.value) || 0;
  const after = parseInt(panel.querySelector('.drum-after')?.value) || 0;
  const diffInput = panel.querySelector('.drum-diff');
  const statusSpan = panel.querySelector('.calib-status');
  if (before > 0 && after > 0) {
    const diff = after - before;
    diffInput.value = (diff >= 0 ? '+' : '') + diff;
    statusSpan.classList.remove('d-none');
    if (Math.abs(diff) <= 2) {
      statusSpan.textContent = 'OK';
      statusSpan.className = 'calib-status pass';
    } else {
      statusSpan.textContent = 'Diff!';
      statusSpan.className = 'calib-status fail';
    }
  } else {
    diffInput.value = '';
    statusSpan.classList.add('d-none');
  }
}

// Analysis Equipment Calibration Check
function checkAnalysisDiff(input) {
  const row = input.closest('tr');
  const certVal = parseFloat(row.querySelector('.calib-cert-val')?.value) || 0;
  const measVal = parseFloat(input.value) || 0;
  const diffInput = row.querySelector('.calib-diff-pct');
  const statusSpan = row.querySelector('.analysis-panel .calib-status');

  if (certVal > 0 && measVal > 0) {
    const diffPct = ((measVal - certVal) / certVal * 100);
    diffInput.value = (diffPct >= 0 ? '+' : '') + diffPct.toFixed(2) + ' %';

    statusSpan.classList.remove('d-none');
    if (Math.abs(diffPct) <= 2) {
      statusSpan.textContent = 'OK';
      statusSpan.className = 'calib-status pass';
    } else {
      statusSpan.textContent = 'Deviation!';
      statusSpan.className = 'calib-status fail';
    }
  } else {
    diffInput.value = '';
    statusSpan.classList.add('d-none');
  }
}

// Sulfur analyzer - standards check
function checkSulfurRow(input) {
  const stdRow = input.closest('.calib-std-row');
  const certVal = parseFloat(stdRow.querySelector('.sulfur-cert-val')?.value) || 0;
  const measVal = parseFloat(input.value) || 0;
  const statusSpan = stdRow.querySelector('.calib-status');

  if (certVal > 0 && measVal > 0) {
    const diffPct = Math.abs((measVal - certVal) / certVal * 100);
    statusSpan.classList.remove('d-none');
    if (diffPct <= 5) {
      statusSpan.textContent = 'OK';
      statusSpan.className = 'calib-status pass';
    } else {
      statusSpan.textContent = diffPct.toFixed(1) + '%';
      statusSpan.className = 'calib-status fail';
    }
  } else {
    statusSpan.classList.add('d-none');
  }
  updateSulfurRMS(input.closest('.sulfur-panel'));
  updateSulfurFinalStatus(input.closest('.sulfur-panel'));
}

function checkSulfurVerifyRow(input) {
  const row = input.closest('.sulfur-check-row');
  const certVal = parseFloat(row.querySelector('.sulfur-chk-cert')?.value) || 0;
  const measVal = parseFloat(input.value) || 0;
  const statusSpan = row.querySelector('.calib-status');

  if (certVal > 0 && measVal > 0) {
    const diffPct = Math.abs((measVal - certVal) / certVal * 100);
    statusSpan.classList.remove('d-none');
    if (diffPct <= 5) {
      statusSpan.textContent = 'OK';
      statusSpan.className = 'calib-status pass';
    } else {
      statusSpan.textContent = diffPct.toFixed(1) + '%';
      statusSpan.className = 'calib-status fail';
    }
  } else {
    statusSpan.classList.add('d-none');
  }
  updateSulfurFinalStatus(input.closest('.sulfur-panel'));
}

// RMS Error = sqrt(sum((meas - cert)^2) / n)
function updateSulfurRMS(panel) {
  if (!panel) return;
  const rmsInput = panel.querySelector('.sulfur-rms');
  var sumSq = 0, n = 0;
  panel.querySelectorAll('.calib-std-row').forEach(row => {
    const meas = parseFloat(row.querySelector('.sulfur-meas-val')?.value);
    const cert = parseFloat(row.querySelector('.sulfur-cert-val')?.value);
    if (!isNaN(meas) && !isNaN(cert) && cert > 0) {
      sumSq += (meas - cert) ** 2;
      n++;
    }
  });
  if (n > 0) {
    const rms = Math.sqrt(sumSq / n);
    rmsInput.value = rms.toFixed(4);
    rmsInput.style.color = rms < 0.05 ? '#15803d' : '#dc2626';
  } else {
    rmsInput.value = '';
  }
}

function addSulfurStdRow(btn) {
  const list = btn.closest('.sulfur-panel').querySelector('.sulfur-stds-list');
  const idx = list.querySelectorAll('.calib-std-row').length + 1;
  const row = document.createElement('div');
  row.className = 'calib-std-row mb-1';
  row.style.cssText = 'display:flex; gap:4px; align-items:center;';
  row.innerHTML =
    '<span style="font-size:0.7rem; min-width:18px; color:#6366f1; font-weight:700;">' + idx + '.</span>' +
    '<input type="text" class="form-control form-control-sm sulfur-std-name" placeholder="—" style="flex:1.5">' +
    '<input type="number" class="form-control form-control-sm sulfur-weight" placeholder="—" step="0.0001" style="flex:1">' +
    '<input type="number" class="form-control form-control-sm sulfur-moisture" placeholder="—" step="0.01" style="flex:0.7">' +
    '<input type="number" class="form-control form-control-sm sulfur-meas-val" placeholder="—" step="0.001" style="flex:0.8" oninput="checkSulfurRow(this)">' +
    '<input type="number" class="form-control form-control-sm sulfur-cert-val" placeholder="—" step="0.001" style="flex:0.8">' +
    '<span class="calib-status d-none" style="min-width:45px;"></span>';
  list.appendChild(row);
}

function addSulfurCheckRow(btn) {
  const list = btn.closest('.sulfur-panel').querySelector('.sulfur-check-list');
  const idx = list.querySelectorAll('.sulfur-check-row').length + 1;
  const row = document.createElement('div');
  row.className = 'sulfur-check-row mb-1';
  row.style.cssText = 'display:flex; gap:4px; align-items:center;';
  row.innerHTML =
    '<span style="font-size:0.7rem; min-width:18px; color:#15803d; font-weight:700;">' + idx + '.</span>' +
    '<input type="text" class="form-control form-control-sm sulfur-chk-name" placeholder="Std ID" style="flex:1.5">' +
    '<input type="number" class="form-control form-control-sm sulfur-chk-weight" placeholder="Wt,g" step="0.0001" style="flex:1">' +
    '<input type="number" class="form-control form-control-sm sulfur-chk-moisture" placeholder="M,%" step="0.01" style="flex:0.7">' +
    '<input type="number" class="form-control form-control-sm sulfur-chk-meas" placeholder="St,d%" step="0.001" style="flex:0.8" oninput="checkSulfurVerifyRow(this)">' +
    '<input type="number" class="form-control form-control-sm sulfur-chk-cert" placeholder="Cert%" step="0.001" style="flex:0.8">' +
    '<span class="calib-status d-none" style="min-width:45px;"></span>';
  list.appendChild(row);
}

function updateSulfurFinalStatus(panel) {
  const T = window.EQ_I18N || {};
  if (!panel) return;
  const finalEl = panel.querySelector('.sulfur-final-status');
  const checkRows = panel.querySelectorAll('.sulfur-check-row');
  var hasData = false, allPass = true;

  checkRows.forEach(row => {
    const meas = parseFloat(row.querySelector('.sulfur-chk-meas')?.value) || 0;
    const cert = parseFloat(row.querySelector('.sulfur-chk-cert')?.value) || 0;
    if (meas > 0 && cert > 0) {
      hasData = true;
      if (Math.abs((meas - cert) / cert * 100) > 5) allPass = false;
    }
  });

  if (hasData) {
    if (allPass) {
      finalEl.innerHTML = '<span style="color:#15803d; background:#dcfce7; padding:4px 12px; border-radius:8px;"><i class="bi bi-check-circle-fill me-1"></i>' + (T.calibVerified || 'Calibration verified') + '</span>';
    } else {
      finalEl.innerHTML = '<span style="color:#dc2626; background:#fee2e2; padding:4px 12px; border-radius:8px;"><i class="bi bi-x-circle-fill me-1"></i>' + (T.verifyFailed || 'Verification failed — recalibrate') + '</span>';
    }
  } else {
    finalEl.innerHTML = '';
  }
}

// Calorimeter — 5 measurements check
function checkCalorimeter(input) {
  const panel = input.closest('.calorimeter-panel');
  const certVal = parseFloat(panel.querySelector('.cal-cert-val')?.value) || 26454;
  const measurements = [...panel.querySelectorAll('.cal-meas')].map(i => parseFloat(i.value) || 0).filter(v => v > 0);

  const avgInput = panel.querySelector('.cal-avg');
  const rsdInput = panel.querySelector('.cal-rsd');
  const statusSpan = panel.querySelector('.calib-status');

  if (measurements.length >= 2) {
    const avg = measurements.reduce((a, b) => a + b, 0) / measurements.length;
    const stdDev = Math.sqrt(measurements.reduce((sum, v) => sum + Math.pow(v - avg, 2), 0) / (measurements.length - 1));
    const rsd = (stdDev / avg) * 100;

    avgInput.value = avg.toFixed(0);
    rsdInput.value = rsd.toFixed(2) + '%';

    const maxErrInput = panel.querySelector('.cal-max-err');
    const maxErr = Math.abs((avg - certVal) / certVal * 100);
    if (maxErrInput) maxErrInput.value = maxErr.toFixed(2) + '%';

    statusSpan.classList.remove('d-none');
    if (rsd <= 0.1 && maxErr <= 0.2) {
      statusSpan.textContent = 'OK';
      statusSpan.className = 'calib-status pass';
    } else {
      statusSpan.textContent = maxErr > 0.2 ? 'Err>' + maxErr.toFixed(1) + '%' : 'RSD!';
      statusSpan.className = 'calib-status fail';
    }
  } else {
    avgInput.value = '';
    rsdInput.value = '';
    const maxErrInput = panel.querySelector('.cal-max-err');
    if (maxErrInput) maxErrInput.value = '';
    statusSpan.classList.add('d-none');
  }
}

function submitEquipmentUsage() {
  const T = window.EQ_I18N || {};
  const rows = document.querySelectorAll('#equipmentCheckTable tbody tr');
  const items = [];

  rows.forEach(row => {
    const eqId = row.dataset.eqId;
    const category = row.dataset.category;
    const isChecked = row.querySelector('.eq-check')?.checked ?? true;
    const minutesVal = row.querySelector('.eq-minutes')?.value;
    const note = row.querySelector('.eq-note')?.value || '';
    const minutes = minutesVal ? parseFloat(minutesVal) : 0;
    const needsRepair = row.querySelector('.eq-repair')?.checked || false;

    const item = {
      eq_id: eqId,
      is_checked: isChecked,
      minutes: minutes,
      note: note
    };

    // Calibration data based on category
    const calibPanel = row.querySelector('.calib-panel:not(.d-none)');
    if (calibPanel) {
      const eqName = (row.dataset.eqName || '').toLowerCase();
      const isTempCheck = (category === 'furnace' || category === 'dryer' || eqName.includes('термостат') || eqName.includes('thermostat'));
      if (isTempCheck) {
        const setTemp = row.querySelector('.calib-set-temp')?.value;
        const actualTemp = row.querySelector('.calib-actual-temp')?.value;
        if (setTemp || actualTemp) {
          item.calibration = {
            type: 'temperature',
            set_temp: parseFloat(setTemp) || null,
            actual_temp: parseFloat(actualTemp) || null
          };
        }
      } else if (category === 'balance') {
        const weights = [];
        row.querySelectorAll('.calib-weight-row').forEach(wr => {
          const std = wr.querySelector('.calib-std-wt')?.value;
          const meas = wr.querySelector('.calib-meas-wt')?.value;
          if (std || meas) {
            weights.push({
              standard: parseFloat(std) || null,
              measured: parseFloat(meas) || null
            });
          }
        });
        const ethVolume = row.querySelector('.ethanol-volume')?.value;
        const ethMeasured = row.querySelector('.ethanol-measured')?.value;
        const ethanol = (ethVolume || ethMeasured) ? {
          temperature: parseFloat(row.querySelector('.ethanol-temp')?.value) || null,
          density: parseFloat(row.querySelector('.ethanol-density')?.value) || null,
          volume: parseFloat(ethVolume) || null,
          expected: parseFloat(row.querySelector('.ethanol-expected')?.value) || null,
          measured: parseFloat(ethMeasured) || null
        } : null;

        if (weights.length > 0 || ethanol) {
          item.calibration = { type: 'weight', weights: weights };
          if (ethanol) item.calibration.ethanol = ethanol;
        }
      } else if (category === 'prep') {
        const before = calibPanel.querySelector('.drum-before')?.value;
        const after = calibPanel.querySelector('.drum-after')?.value;
        const duration = calibPanel.querySelector('.drum-duration')?.value;
        if (before || after) {
          item.calibration = {
            type: 'drum',
            duration: duration || null,
            before: parseInt(before) || null,
            after: parseInt(after) || null
          };
        }
      } else if (category === 'analysis') {
        const calibType = calibPanel.dataset.calibType;

        if (calibType === 'sulfur' || calibType === 'xrf_calib') {
          const curveType = calibPanel.querySelector('.sulfur-curve-type')?.value;
          const standards = [];
          calibPanel.querySelectorAll('.calib-std-row').forEach(stdRow => {
            const name = stdRow.querySelector('.sulfur-std-name')?.value;
            const weight = stdRow.querySelector('.sulfur-weight')?.value;
            const moisture = stdRow.querySelector('.sulfur-moisture')?.value;
            const meas = stdRow.querySelector('.sulfur-meas-val')?.value;
            const cert = stdRow.querySelector('.sulfur-cert-val')?.value;
            if (name || cert || meas) {
              standards.push({
                name: name || null,
                weight: parseFloat(weight) || null,
                moisture: parseFloat(moisture) || null,
                measured: parseFloat(meas) || null,
                certified: parseFloat(cert) || null
              });
            }
          });
          const verifications = [];
          calibPanel.querySelectorAll('.sulfur-check-row').forEach(row => {
            const name = row.querySelector('.sulfur-chk-name')?.value;
            const weight = row.querySelector('.sulfur-chk-weight')?.value;
            const moisture = row.querySelector('.sulfur-chk-moisture')?.value;
            const meas = row.querySelector('.sulfur-chk-meas')?.value;
            const cert = row.querySelector('.sulfur-chk-cert')?.value;
            if (name || cert || meas) {
              verifications.push({
                name: name || null,
                weight: parseFloat(weight) || null,
                moisture: parseFloat(moisture) || null,
                measured: parseFloat(meas) || null,
                certified: parseFloat(cert) || null
              });
            }
          });
          if (standards.length > 0 || verifications.length > 0) {
            const rmsVal = calibPanel.querySelector('.sulfur-rms')?.value;
            item.calibration = {
              type: calibType,
              curve_type: curveType,
              rms_error: parseFloat(rmsVal) || null,
              standards: standards,
              verifications: verifications
            };
          }
        } else if (calibType === 'calorimeter') {
          const vessel = calibPanel.querySelector('.cal-vessel')?.value;
          const stdName = calibPanel.querySelector('.cal-std-name')?.value;
          const certVal = calibPanel.querySelector('.cal-cert-val')?.value;
          const prevCap = calibPanel.querySelector('.cal-prev-capacity')?.value;
          const bombCap = calibPanel.querySelector('.cal-bomb-capacity')?.value;
          const measurements = [...calibPanel.querySelectorAll('.cal-meas')].map(i => parseFloat(i.value) || null).filter(v => v !== null);
          if (measurements.length > 0) {
            item.calibration = {
              type: 'calorimeter',
              vessel: vessel || '1',
              standard_name: stdName || 'Benzoic Acid',
              certified_value: parseFloat(certVal) || 26460,
              prev_heat_capacity: parseFloat(prevCap) || null,
              bomb_heat_capacity: parseFloat(bombCap) || null,
              measurements: measurements
            };
          }
        } else if (calibType === 'csn_crucible') {
          const startTemp = calibPanel.querySelector('.csn-start-temp')?.value;
          const maxCurrent = calibPanel.querySelector('.csn-max-current')?.value;
          const tests = [];
          const adjustments = [];

          calibPanel.querySelectorAll('.csn-crucible-list > *').forEach(el => {
            if (el.classList.contains('csn-crucible-row')) {
              const t1 = el.querySelector('.csn-temp-1min')?.value;
              const t2 = el.querySelector('.csn-temp-1m30')?.value;
              const t3 = el.querySelector('.csn-temp-2m30')?.value;
              const status = el.querySelector('.csn-row-status')?.textContent || '';
              if (t1 || t2 || t3) {
                tests.push({
                  temp_1min: parseFloat(t1) || null,
                  temp_1m30: parseFloat(t2) || null,
                  temp_2m30: parseFloat(t3) || null,
                  pass: status.includes('OK')
                });
              }
            } else if (el.classList.contains('csn-adjust-row')) {
              const adjTemp = el.querySelector('.csn-adj-temp')?.value;
              const adjCurr = el.querySelector('.csn-adj-current')?.value;
              if (adjTemp || adjCurr) {
                adjustments.push({
                  start_temp: parseFloat(adjTemp) || null,
                  max_current_sec: parseFloat(adjCurr) || null
                });
              }
            }
          });

          if (tests.length > 0) {
            item.calibration = {
              type: 'csn_crucible',
              start_temp: parseFloat(startTemp) || null,
              max_current_sec: parseFloat(maxCurrent) || null,
              tests: tests,
              adjustments: adjustments,
              final_pass: tests.length > 0 && tests[tests.length - 1].pass
            };
          }
        } else if (calibType === 'drum') {
          const initial = calibPanel.querySelector('.drum-initial')?.value;
          const meas1 = calibPanel.querySelector('.drum-meas-1min')?.value;
          const meas5 = calibPanel.querySelector('.drum-meas-5min')?.value;
          if (meas1 || meas5) {
            const m1 = parseInt(meas1) || 0;
            const m5 = parseInt(meas5) || 0;
            item.calibration = {
              type: 'drum',
              initial_rpm: parseInt(initial) || null,
              meas_1min: m1 || null,
              meas_5min: m5 || null,
              target_1min: 50,
              target_5min: 250,
              pass: (m1 === 50 && m5 === 250)
            };
          }
        } else {
          const stdName = row.querySelector('.calib-std-name')?.value;
          const certVal = row.querySelector('.calib-cert-val')?.value;
          const measVal = row.querySelector('.calib-meas-val')?.value;
          if (stdName || certVal || measVal) {
            item.calibration = {
              type: 'analysis',
              standard_name: stdName || null,
              certified_value: parseFloat(certVal) || null,
              measured_value: parseFloat(measVal) || null
            };
          }
        }
      }
      // Calibration frequency
      if (item.calibration) {
        const freqSel = calibPanel.querySelector('.calib-freq');
        if (freqSel) item.calibration.frequency = freqSel.value;
      }
    }

    if (needsRepair) {
      item.repair = true;
      item.repair_date = row.querySelector('.repair-date')?.value || '';
      const spares = [];
      row.querySelectorAll('.spare-row').forEach(sr => {
        const spareId = sr.querySelector('.spare-select')?.value;
        const qty = sr.querySelector('.spare-qty')?.value;
        const user = sr.querySelector('.spare-user')?.value || '';
        if (spareId) {
          spares.push({ spare_id: parseInt(spareId), qty: parseInt(qty) || 1, used_by: user });
        }
      });
      item.spare_parts = spares;
    }

    if (minutes > 0 || note.trim() !== '' || needsRepair || item.calibration) {
      items.push(item);
    }
  });

  if (items.length === 0) {
    alert(T.noDataToSave || 'No data to save.');
    return;
  }

  fetch('/api/log_usage_bulk', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-TOKEN': window.csrfToken || ''
    },
    body: JSON.stringify({ items: items })
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'success') {
      document.querySelectorAll('.eq-minutes').forEach(i => i.value = '');
      document.querySelectorAll('.eq-note').forEach(i => i.value = '');
      document.querySelectorAll('.eq-repair').forEach(cb => { cb.checked = false; toggleRepairPanel(cb); });
      document.querySelectorAll('.calib-panel').forEach(p => {
        p.classList.add('d-none');
        p.querySelectorAll('input').forEach(i => i.value = '');
        p.querySelectorAll('.calib-status').forEach(s => s.classList.add('d-none'));
      });
      document.querySelectorAll('.calib-btn').forEach(btn => {
        btn.classList.remove('btn-success');
        btn.classList.add('btn-outline-success');
      });

      var modal = bootstrap.Modal.getInstance(document.getElementById('equipmentModal'));
      if (modal) modal.hide();

      alert(T.savedSuccess || 'Equipment usage saved successfully!');
    } else {
      alert((T.errorColon || 'Error:') + ' ' + (data.message || (T.unknownError || 'Unknown error')));
    }
  })
  .catch(err => {
    console.error('Equipment usage error:', err);
    alert(T.serverError || 'Server error!');
  });
}

// ── Delegated CSP-compatible handlers ─────────────────────────────────────
// analysis_page.html дээр байсан inline oninput/onclick/onchange-г орлоно.
// Template-д зөвхөн класс/id тавьж, бүх event-ийн routing энд байрлана.
(function () {
  // Input handlers: class → handler function
  const INPUT_CLASS_HANDLERS = {
    'calib-actual-temp': checkTempDiff,
    'calib-meas-wt':     checkWeightDiff,
    'ethanol-temp':      calcEthanol,
    'ethanol-density':   calcEthanol,
    'ethanol-volume':    calcEthanol,
    'ethanol-measured':  calcEthanol,
    'drum-before':       checkDrumDiff,
    'drum-after':        checkDrumDiff,
    'sulfur-meas-val':   checkSulfurRow,
    'sulfur-chk-meas':   checkSulfurVerifyRow,
    'cal-meas':          checkCalorimeter,
    'csn-temp-1min':     checkCsnTemp,
    'csn-temp-1m30':     checkCsnTemp,
    'csn-temp-2m30':     checkCsnTemp,
    'drum-meas-1min':    checkDrumRow,
    'drum-meas-5min':    checkDrumRow,
    'calib-meas-val':    checkAnalysisDiff,
  };

  document.addEventListener('input', function (e) {
    const el = e.target;
    if (!(el instanceof HTMLInputElement)) return;
    for (const cls in INPUT_CLASS_HANDLERS) {
      if (el.classList.contains(cls)) {
        INPUT_CLASS_HANDLERS[cls](el);
        break;
      }
    }
  });

  document.addEventListener('change', function (e) {
    const el = e.target;
    if (el instanceof HTMLInputElement && el.classList.contains('eq-repair-cb')) {
      toggleRepairPanel(el);
    }
  });

  document.addEventListener('click', function (e) {
    const t = e.target;
    // Calibration toggle
    const calibBtn = t.closest('.calib-btn');
    if (calibBtn) { toggleCalibPanel(calibBtn); return; }
    // Add-row buttons
    const addBtn = t.closest('.js-add-weight-row, .js-add-sulfur-std, .js-add-sulfur-check, .js-add-csn-retest, [data-action="add-spare-part"]');
    if (addBtn) {
      if (addBtn.classList.contains('js-add-weight-row')) addWeightRow(addBtn);
      else if (addBtn.classList.contains('js-add-sulfur-std')) addSulfurStdRow(addBtn);
      else if (addBtn.classList.contains('js-add-sulfur-check')) addSulfurCheckRow(addBtn);
      else if (addBtn.classList.contains('js-add-csn-retest')) addCsnRetest(addBtn);
      else if (addBtn.dataset.action === 'add-spare-part') addSparePart(addBtn);
      return;
    }
    // Submit equipment usage
    if (t.closest('#btn-submit-equipment')) {
      submitEquipmentUsage();
    }
  });
})();
