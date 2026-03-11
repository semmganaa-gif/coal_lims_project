/* ahlah_dashboard_page.js — Senior Dashboard page logic (extracted from ahlah_dashboard.html) */
/* Requires: window.AHLAH_KPI_SUMMARY_URL, window.AHLAH_STATS_URL, window.AHLAH_DATA_URL,
             window.ERROR_LABELS, I18N object */

document.addEventListener('DOMContentLoaded', function() {
  loadResults();
  loadKpiSummary();
  loadAhlahStats();
});

function loadResults() {
  const urlParams = new URLSearchParams(window.location.search);
  const apiUrl = window.AHLAH_DATA_URL + '?' + urlParams.toString();

  fetch(apiUrl)
    .then(res => res.json())
    .then(data => {
      renderResults(data);
      updateMetrics(data);
    })
    .catch(err => {
      console.error('Үр дүн ачаалахад алдаа:', err);
      document.getElementById('results-container').innerHTML = `
        <div class="empty-state">
          <i class="bi bi-exclamation-triangle"></i>
          <h5>${I18N.errorOccurred}</h5>
          <p>${I18N.couldNotLoadData}</p>
        </div>
      `;
    });
}

function renderResults(data) {
  const container = document.getElementById('results-container');

  if (!data || data.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="bi bi-inbox"></i>
        <h5>${I18N.noResultsToReview}</h5>
        <p>${I18N.noResultsCurrently}</p>
      </div>
    `;
    return;
  }

  let html = '';
  data.forEach((item, idx) => {
    html += renderResultCard(item, idx);
  });
  container.innerHTML = html;

  // Event listeners
  container.querySelectorAll('.btn-approve').forEach(btn => {
    btn.addEventListener('click', function() {
      const id = this.dataset.id;
      if (confirm(I18N.approveThisResult)) {
        approveResult(id);
      }
    });
  });

  container.querySelectorAll('.btn-reject').forEach(btn => {
    btn.addEventListener('click', function() {
      document.getElementById('reject-result-id').value = this.dataset.id;
      document.getElementById('reject-sample-info').textContent =
        this.dataset.sampleCode + ' / ' + this.dataset.analysisName;
    });
  });
}

function renderResultCard(item, idx) {
  const statusClass = item.status === 'rejected' ? 'rejected' : 'pending';
  const statusText = item.status === 'rejected' ? I18N.rejected : I18N.pending;
  const raw = item.raw_data || {};

  // Parallel data
  let parallelHtml = '';
  const code = item.analysis_code || '';

  // MG tube
  if (raw.empty_crucible !== undefined || raw.mg_mass !== undefined) {
    parallelHtml = `
      <table class="parallel-table">
        <thead><tr>
          <th>${I18N.emptyWeight}</th><th>${I18N.sampleWeight}</th><th>${I18N.driedWeight}</th>
          <th>MG(g)</th><th>NoMG(g)</th><th>MG%</th>
        </tr></thead>
        <tbody><tr>
          <td>${formatNum(raw.empty_crucible, 2)}</td>
          <td>${formatNum(raw.sample_mass, 1)}</td>
          <td>${formatNum(raw.dried_weight, 2)}</td>
          <td><strong>${formatNum(raw.mg_mass, 2)}</strong></td>
          <td>${formatNum(raw.nomg_mass, 2)}</td>
          <td><strong>${formatNum(raw.mg_pct, 2)}</strong></td>
        </tr></tbody>
      </table>
    `;
  }
  // MG_SIZE fractions
  else if (Array.isArray(raw.fractions) && raw.fractions.length) {
    parallelHtml = `
      <table class="parallel-table">
        <thead><tr>
          <th>${I18N.fraction}</th><th>m2(g)</th><th>m3(g)</th><th>g</th><th>%</th>
        </tr></thead>
        <tbody>
          ${raw.fractions.map(f => `
            <tr>
              <td class="row-label">${escapeHtml(f.label) || '-'}</td>
              <td>${formatNum(f.m2, 1)}</td>
              <td>${formatNum(f.m3, 1)}</td>
              <td>${formatNum(f.m1, 1)}</td>
              <td><strong>${formatNum(f.pct, 1)}</strong></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }
  // Standard p1/p2/p3 parallel format
  else {
    const parallels = raw.parallels || [];
    if (parallels.length === 0) {
      ['p1', 'p2', 'p3'].forEach(key => {
        if (raw[key] && typeof raw[key] === 'object' && Object.keys(raw[key]).length > 0) {
          parallels.push({ label: key.toUpperCase(), ...raw[key] });
        }
      });
    }
    // Flat m1/m2/m3 format
    if (parallels.length === 0 && (raw.m1 !== undefined || raw.m2 !== undefined || raw.result !== undefined)) {
      parallels.push({ label: '1', ...raw });
    }

    if (parallels.length > 0) {
      const isMgTrd = code === 'MG_TRD';
      const headers = isMgTrd
        ? '<th>#</th><th>Pyc</th><th>m(g)</th><th>m2(g)</th><th>m1(g)</th><th>TRD</th>'
        : '<th>#</th><th>m1</th><th>m2</th><th>m3</th><th>' + I18N.result + '</th>';
      const rowFn = isMgTrd
        ? p => `<td class="row-label">${escapeHtml(p.label || p.num) || '-'}</td>
                <td>${formatNum(p.pycno, 0)}</td><td>${formatNum(p.m)}</td>
                <td>${formatNum(p.m2)}</td><td>${formatNum(p.m1)}</td>
                <td><strong>${formatNum(p.result, 3)}</strong></td>`
        : p => `<td class="row-label">${escapeHtml(p.label || p.num) || '-'}</td>
                <td>${formatNum(p.m1)}</td><td>${formatNum(p.m2)}</td>
                <td>${formatNum(p.m3)}</td>
                <td><strong>${formatNum(p.result, 3)}</strong></td>`;

      parallelHtml = `
        <table class="parallel-table">
          <thead><tr>${headers}</tr></thead>
          <tbody>
            ${parallels.map(p => `<tr>${rowFn(p)}</tr>`).join('')}
          </tbody>
        </table>
      `;
    }
  }

  // Summary values
  const avg = raw.avg;
  const diff = raw.diff;
  const finalVal = item.final_value;

  // User initials
  const initials = (item.user_name || 'XX').substring(0, 2).toUpperCase();

  // Error badge
  let errorBadge = '';
  if (item.status === 'rejected' && item.error_reason) {
    const errorText = window.ERROR_LABELS[item.error_reason] || item.error_reason;
    errorBadge = `<div class="mt-2"><span class="badge bg-danger">${escapeHtml(errorText)}</span></div>`;
  }

  return `
    <div class="result-card ${statusClass}" style="animation-delay: ${idx * 0.1}s; position: relative;" data-result-id="${item.result_id}">
      <div class="result-checkbox">
        <input type="checkbox" class="result-select-cb" data-id="${item.result_id}">
      </div>
      <div class="result-card-header">
        <div class="result-sample-info">
          <div class="result-sample-code">${escapeHtml(item.sample_code)}</div>
          <div class="result-analysis-name">${escapeHtml(item.analysis_name)}</div>
          ${errorBadge}
        </div>
        <span class="result-status-badge ${statusClass}">${statusText}</span>
      </div>

      <div class="result-card-body">
        ${parallelHtml ? `
          <div class="raw-data-section">
            <div class="raw-data-title">
              <i class="bi bi-table"></i> ${I18N.parallelMeasurements}
            </div>
            ${parallelHtml}
          </div>
        ` : ''}

        <div class="summary-row">
          ${avg !== undefined && avg !== null ? `
            <div class="summary-item">
              <div class="summary-item-label">${I18N.average}</div>
              <div class="summary-item-value avg">${formatNum(avg, 3)}</div>
            </div>
          ` : ''}
          ${diff !== undefined && diff !== null ? `
            <div class="summary-item">
              <div class="summary-item-label">${I18N.toleranceT}</div>
              <div class="summary-item-value diff">${formatNum(diff, 4)}</div>
            </div>
          ` : ''}
          ${finalVal !== undefined && finalVal !== null ? `
            <div class="summary-item">
              <div class="summary-item-label">${I18N.finalResult}</div>
              <div class="summary-item-value final">${formatNum(finalVal, 3)}</div>
            </div>
          ` : ''}
        </div>

        <div class="result-meta">
          <div class="result-user">
            <div class="result-user-avatar">${initials}</div>
            <div class="result-user-info">
              <div class="result-user-name">${escapeHtml(item.user_name)}</div>
              <div class="result-user-date">${item.updated_at || '-'}</div>
            </div>
          </div>

          <div class="result-actions">
            <button type="button" class="btn-action approve btn-approve" data-id="${item.result_id}">
              <i class="bi bi-check-lg"></i> ${I18N.approve}
            </button>
            <button type="button" class="btn-action reject btn-reject"
              data-id="${item.result_id}"
              data-sample-code="${escapeHtml(item.sample_code)}"
              data-analysis-name="${escapeHtml(item.analysis_name)}"
              data-bs-toggle="modal" data-bs-target="#rejectModal">
              <i class="bi bi-x-lg"></i> ${I18N.reject}
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
}

function formatNum(val, precision) {
  if (precision === undefined) precision = 4;
  if (val === undefined || val === null || val === '') return '-';
  const num = Number(val);
  if (isNaN(num)) return escapeHtml(val);
  return num.toFixed(precision);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function updateMetrics(data) {
  const total = data.length;
  const pending = data.filter(d => d.status === 'pending_review').length;
  const rejected = data.filter(d => d.status === 'rejected').length;

  document.getElementById('metric-total').textContent = total;
  document.getElementById('metric-pending').textContent = pending;
  document.getElementById('metric-rejected').textContent = rejected;

  const now = new Date();
  document.getElementById('metrics-refresh').textContent =
    I18N.updated + ': ' + now.toLocaleString('en-US', { hour12: false });
}

function loadKpiSummary() {
  if (!window.AHLAH_KPI_SUMMARY_URL) return;

  fetch(window.AHLAH_KPI_SUMMARY_URL)
    .then(res => res.json())
    .then(data => {
      if (data.shift) {
        document.getElementById('kpi-shift-total').textContent = data.shift.total_errors || 0;
      }
      if (data.days14) {
        document.getElementById('kpi-14d-total').textContent = data.days14.total_errors || 0;
      }
    })
    .catch(err => console.error('KPI load error:', err));
}

function loadAhlahStats() {
  if (!window.AHLAH_STATS_URL) return;

  fetch(window.AHLAH_STATS_URL)
    .then(res => res.json())
    .then(data => {
      if (!data) return;

      if (data.summary) {
        const approved = document.getElementById('metric-approved');
        if (approved) approved.textContent = data.summary.approved || 0;
      }

      const samplesBadge = document.getElementById('samples-total-badge');
      if (samplesBadge) samplesBadge.textContent = (data.samples_today || 0) + ' ' + I18N.samples;

      renderSamplesByUnit(data.samples_by_unit || []);
      renderSamplesByType(data.samples_by_type || []);
      renderChemistStats(data.chemists || []);
      renderAnalysisStats(data.analysis_types || []);
    })
    .catch(err => console.error('Stats load error:', err));
}

function renderSamplesByUnit(units) {
  const container = document.getElementById('sidebar-samples-unit');
  const badge = document.getElementById('samples-total-badge');

  if (badge) {
    const total = units.reduce((sum, u) => sum + u.count, 0);
    badge.textContent = total;
  }

  if (container) {
    if (units.length === 0) {
      container.innerHTML = '<div class="metric-expand-empty">' + I18N.noSamplesRegisteredToday + '</div>';
    } else {
      let html = '';
      units.forEach(function(u) {
        html += `
          <div class="metric-expand-item">
            <span class="metric-expand-name">${escapeHtml(u.name)}</span>
            <span class="metric-expand-count">${u.count}</span>
          </div>
        `;
      });
      container.innerHTML = html;
    }
  }
}

function renderSamplesByType(types) {
  const container = document.getElementById('sidebar-samples-type');
  const badge = document.getElementById('samples-type-badge');

  if (badge) {
    badge.textContent = types.length;
  }

  if (container) {
    if (types.length === 0) {
      container.innerHTML = '<div class="metric-expand-empty">' + I18N.noSamplesRegisteredToday + '</div>';
    } else {
      let html = '';
      types.forEach(function(t) {
        html += `
          <div class="metric-expand-item">
            <span class="metric-expand-name">${escapeHtml(t.name)}</span>
            <span class="metric-expand-count">${t.count}</span>
          </div>
        `;
      });
      container.innerHTML = html;
    }
  }
}

function renderChemistStats(chemists) {
  const container = document.getElementById('chemist-stats-list');
  const badge = document.getElementById('chemist-total-badge');

  if (!container) return;

  if (badge) {
    badge.textContent = chemists.length + ' ' + I18N.chemists;
  }

  if (chemists.length === 0) {
    container.innerHTML = `
      <div class="stats-empty">
        <i class="bi bi-inbox"></i>
        ${I18N.noAnalysesPerformedToday}
      </div>
    `;
    return;
  }

  let html = '';
  chemists.forEach(function(c) {
    const initials = (c.username || 'XX').substring(0, 2).toUpperCase();
    html += `
      <div class="stats-item">
        <div class="stats-item-name">
          <div class="stats-item-avatar">${initials}</div>
          <span>${escapeHtml(c.username)}</span>
        </div>
        <div class="stats-item-counts">
          <span class="stats-count total" title="${I18N.total}">${c.total}</span>
          <span class="stats-count approved" title="${I18N.approved}">${c.approved}</span>
          <span class="stats-count pending" title="${I18N.pendingTitle}">${c.pending}</span>
          ${c.rejected > 0 ? `<span class="stats-count rejected" title="${I18N.rejectedTitle}">${c.rejected}</span>` : ''}
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function renderAnalysisStats(analysisTypes) {
  const container = document.getElementById('analysis-stats-list');
  const badge = document.getElementById('analysis-total-badge');

  if (!container) return;

  if (badge) {
    badge.textContent = analysisTypes.length + ' ' + I18N.types;
  }

  if (analysisTypes.length === 0) {
    container.innerHTML = `
      <div class="stats-empty">
        <i class="bi bi-inbox"></i>
        ${I18N.noAnalysesToday}
      </div>
    `;
    return;
  }

  let html = '';
  analysisTypes.forEach(function(a) {
    html += `
      <div class="stats-item">
        <div class="stats-item-name">
          <div class="stats-item-avatar">${escapeHtml(a.code.substring(0, 2))}</div>
          <span>${escapeHtml(a.name)} <small class="text-muted">(${escapeHtml(a.code)})</small></span>
        </div>
        <div class="stats-item-counts">
          <span class="stats-count total" title="${I18N.total}">${a.total}</span>
          <span class="stats-count approved" title="${I18N.approved}">${a.approved}</span>
          <span class="stats-count pending" title="${I18N.pendingTitle}">${a.pending}</span>
          ${a.rejected > 0 ? `<span class="stats-count rejected" title="${I18N.rejectedTitle}">${a.rejected}</span>` : ''}
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function approveResult(id) {
  var csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  fetch('/api/update_result_status/' + id + '/approved', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken }
  })
  .then(res => res.json())
  .then(data => {
    if (data.message === 'OK') {
      location.reload();
    } else {
      alert(data.message || I18N.errorOccurred);
    }
  })
  .catch(err => {
    console.error(err);
    alert(I18N.errorOccurred);
  });
}

// Reject form submit
document.getElementById('reject-form').addEventListener('submit', function(e) {
  e.preventDefault();

  const id = document.getElementById('reject-result-id').value;
  const cat = document.getElementById('rejection_category').value;
  const catText = document.querySelector('#rejection_category option:checked').textContent;

  if (!cat) {
    alert(I18N.selectRejectionReason);
    return;
  }

  const btn = this.querySelector('button[type="submit"]');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> ' + I18N.processing;

  var csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  fetch('/api/update_result_status/' + id + '/rejected', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({
      rejection_category: cat,
      rejection_comment: catText,
      error_reason: cat
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.message === 'OK') {
      bootstrap.Modal.getInstance(document.getElementById('rejectModal')).hide();
      location.reload();
    } else {
      alert(data.message || I18N.errorOccurred);
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-x-circle me-1"></i> ' + I18N.reject;
    }
  })
  .catch(err => {
    console.error(err);
    alert(I18N.errorOccurred);
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-x-circle me-1"></i> ' + I18N.reject;
  });
});

// Set default shift date
(function() {
  const startDate = document.querySelector('input[name="start_date"]');
  const endDate = document.querySelector('input[name="end_date"]');
  const shiftDate = window.getShiftDate ? window.getShiftDate() : null;
  if (shiftDate) {
    if (startDate && !startDate.value) startDate.value = shiftDate;
    if (endDate && !endDate.value) endDate.value = shiftDate;
  }
})();

// ============================================
// BULK OPERATIONS
// ============================================
var selectedResultIds = new Set();

function updateBulkToolbar() {
  const toolbar = document.getElementById('bulk-toolbar');
  const countSpan = document.getElementById('selected-count');
  const selectAllCb = document.getElementById('select-all-results');

  if (selectedResultIds.size > 0) {
    toolbar.style.display = 'flex';
    countSpan.textContent = selectedResultIds.size;
  } else {
    toolbar.style.display = 'none';
  }

  const allCheckboxes = document.querySelectorAll('.result-select-cb');
  if (allCheckboxes.length > 0 && selectedResultIds.size === allCheckboxes.length) {
    selectAllCb.checked = true;
    selectAllCb.indeterminate = false;
  } else if (selectedResultIds.size > 0) {
    selectAllCb.checked = false;
    selectAllCb.indeterminate = true;
  } else {
    selectAllCb.checked = false;
    selectAllCb.indeterminate = false;
  }
}

// Event delegation for checkboxes
document.addEventListener('change', function(e) {
  if (e.target.classList.contains('result-select-cb')) {
    const id = e.target.dataset.id;
    const card = e.target.closest('.result-card');
    if (e.target.checked) {
      selectedResultIds.add(id);
      card.classList.add('selected');
    } else {
      selectedResultIds.delete(id);
      card.classList.remove('selected');
    }
    updateBulkToolbar();
  }
});

// Select All
document.getElementById('select-all-results').addEventListener('change', function() {
  const checkboxes = document.querySelectorAll('.result-select-cb');
  checkboxes.forEach(cb => {
    cb.checked = this.checked;
    const card = cb.closest('.result-card');
    if (this.checked) {
      selectedResultIds.add(cb.dataset.id);
      card.classList.add('selected');
    } else {
      selectedResultIds.delete(cb.dataset.id);
      card.classList.remove('selected');
    }
  });
  updateBulkToolbar();
});

// Clear Selection
document.getElementById('clear-selection-btn').addEventListener('click', function() {
  selectedResultIds.clear();
  document.querySelectorAll('.result-select-cb').forEach(cb => {
    cb.checked = false;
    cb.closest('.result-card').classList.remove('selected');
  });
  updateBulkToolbar();
});

// Bulk Approve
document.getElementById('bulk-approve-btn').addEventListener('click', function() {
  if (selectedResultIds.size === 0) return;
  if (!confirm(selectedResultIds.size + ' - ' + I18N.approveResultsConfirm)) return;

  const btn = this;
  btn.disabled = true;
  btn.innerHTML = '<i class="bi bi-hourglass-split"></i> ' + I18N.pleaseWait;

  fetch('/bulk_update_status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      result_ids: Array.from(selectedResultIds),
      status: 'approved'
    })
  })
  .then(r => r.json())
  .then(data => {
    alert(data.message);
    if (data.success_count > 0) location.reload();
    else {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-check-all"></i> ' + I18N.approveAll;
    }
  })
  .catch(err => {
    alert(I18N.error + ': ' + err);
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-check-all"></i> ' + I18N.approveAll;
  });
});

// Bulk Reject - Open Modal
document.getElementById('bulk-reject-btn').addEventListener('click', function() {
  document.getElementById('bulk-reject-count').textContent = selectedResultIds.size;
});

// Confirm Bulk Reject
document.getElementById('confirm-bulk-reject-btn').addEventListener('click', function() {
  const category = document.getElementById('bulk-rejection-category').value;
  const comment = document.getElementById('bulk-rejection-comment').value;

  if (!category) {
    alert(I18N.selectRejectionReason);
    return;
  }

  const btn = this;
  btn.disabled = true;
  btn.innerHTML = '<i class="bi bi-hourglass-split"></i> ' + I18N.pleaseWait;

  fetch('/bulk_update_status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      result_ids: Array.from(selectedResultIds),
      status: 'rejected',
      rejection_category: category,
      rejection_comment: comment
    })
  })
  .then(r => r.json())
  .then(data => {
    alert(data.message);
    if (data.success_count > 0) location.reload();
    else {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-x-circle me-1"></i> ' + I18N.reject;
    }
  })
  .catch(err => {
    alert(I18N.error + ': ' + err);
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-x-circle me-1"></i> ' + I18N.reject;
  });
});
