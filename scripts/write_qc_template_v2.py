"""Write new QC Control Charts template with filters"""

template = '''{% extends "base.html" %}

{% block content %}
<style>
  :root {
    --glass-bg: rgba(255, 255, 255, 0.75);
    --glass-border: rgba(148, 163, 184, 0.2);
    --shadow-soft: 0 8px 32px rgba(0, 0, 0, 0.08);
    --text-primary: #0f172a;
    --text-muted: #64748b;
    --accent-blue: #3b82f6;
    --accent-green: #22c55e;
    --accent-purple: #8b5cf6;
    --accent-orange: #f59e0b;
    --accent-red: #ef4444;
    --accent-cyan: #06b6d4;
  }

  .qc-dashboard {
    min-height: calc(100vh - 80px);
    padding: 1.5rem;
    background: linear-gradient(135deg, #ecfdf5 0%, #f0f9ff 30%, #faf5ff 60%, #fff7ed 100%);
    background-attachment: fixed;
  }

  .qc-header {
    background: linear-gradient(135deg, rgba(139,92,246,0.12), rgba(59,130,246,0.1), rgba(6,182,212,0.08));
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.4);
    border-radius: 24px;
    padding: 1.25rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    box-shadow: 0 4px 24px rgba(139,92,246,0.1);
  }
  .qc-header h1 {
    font-size: 1.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 50%, #0891b2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
  }
  .qc-header .subtitle { font-size: 0.85rem; color: var(--text-muted); margin-top: 4px; }

  /* Filter buttons */
  .filter-group {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  .filter-btn {
    padding: 8px 16px;
    border-radius: 50px;
    font-weight: 600;
    font-size: 0.8rem;
    border: 2px solid transparent;
    background: rgba(255,255,255,0.8);
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-btn:hover {
    background: rgba(139,92,246,0.1);
    color: var(--accent-purple);
  }
  .filter-btn.active {
    background: var(--accent-purple);
    color: #fff;
    border-color: var(--accent-purple);
  }
  .btn-refresh {
    padding: 10px 20px;
    border-radius: 50px;
    font-weight: 600;
    border: none;
    background: rgba(255,255,255,0.8);
    color: var(--accent-purple);
    cursor: pointer;
    transition: all 0.3s ease;
  }
  .btn-refresh:hover { background: var(--accent-purple); color: #fff; }

  /* Summary cards */
  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  .summary-card {
    background: var(--glass-bg);
    backdrop-filter: blur(16px);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 1rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
  }
  .summary-card:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
  .summary-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; }
  .summary-card.total::before { background: linear-gradient(90deg, #3b82f6, #06b6d4); }
  .summary-card.pass::before { background: linear-gradient(90deg, #22c55e, #4ade80); }
  .summary-card.warning::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
  .summary-card.fail::before { background: linear-gradient(90deg, #ef4444, #f87171); }
  .summary-card.retest::before { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
  .summary-card.rejected::before { background: linear-gradient(90deg, #6b7280, #9ca3af); }
  .summary-label { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); }
  .summary-value { font-size: 1.5rem; font-weight: 800; line-height: 1.2; margin-top: 4px; }
  .summary-card.total .summary-value { color: #1d4ed8; }
  .summary-card.pass .summary-value { color: #16a34a; }
  .summary-card.warning .summary-value { color: #b45309; }
  .summary-card.fail .summary-value { color: #dc2626; }
  .summary-card.retest .summary-value { color: #2563eb; }
  .summary-card.rejected .summary-value { color: #6b7280; }

  /* Standard sections */
  .standards-container { display: flex; flex-direction: column; gap: 1.5rem; }
  .standard-section {
    background: var(--glass-bg);
    backdrop-filter: blur(16px);
    border: 1px solid var(--glass-border);
    border-radius: 24px;
    overflow: hidden;
    box-shadow: var(--shadow-soft);
  }
  .standard-header { padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center; color: #fff; }
  .standard-header.gbw { background: linear-gradient(135deg, #0891b2 0%, #06b6d4 50%, #22d3ee 100%); }
  .standard-header.cm { background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 50%, #a78bfa 100%); }
  .standard-title { font-weight: 700; font-size: 1.1rem; display: flex; align-items: center; gap: 10px; }
  .standard-badge { background: rgba(255,255,255,0.25); padding: 6px 14px; border-radius: 50px; font-size: 0.8rem; font-weight: 600; }

  /* Legend */
  .chart-legend {
    display: flex;
    gap: 1.5rem;
    padding: 0.75rem 1.5rem;
    background: rgba(248,250,252,0.8);
    border-bottom: 1px solid var(--glass-border);
    flex-wrap: wrap;
  }
  .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: var(--text-muted); }
  .legend-dot { width: 10px; height: 10px; border-radius: 50%; }
  .legend-dot.ok { background: #22c55e; }
  .legend-dot.warning { background: #f59e0b; }
  .legend-dot.out { background: #ef4444; }
  .legend-dot.retest { background: #3b82f6; border: 2px solid #1d4ed8; }
  .legend-line { width: 24px; height: 3px; border-radius: 2px; }
  .legend-line.target { background: #1e293b; }
  .legend-line.sd1 { background: #22c55e; }
  .legend-line.sd2 { background: #ef4444; }

  /* Chart cards */
  .charts-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 1rem; padding: 1.25rem; }
  .chart-card {
    background: #fff;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
    transition: all 0.3s ease;
    cursor: pointer;
  }
  .chart-card:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); border-color: var(--accent-purple); }
  .chart-card-header {
    padding: 0.75rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #f8fafc, #f1f5f9);
    border-bottom: 1px solid #e2e8f0;
  }
  .chart-card-title { font-weight: 700; font-size: 0.95rem; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }
  .chart-card-title .code { background: linear-gradient(135deg, #7c3aed, #3b82f6); color: #fff; padding: 3px 10px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; }
  .status-badge { padding: 4px 12px; border-radius: 50px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
  .status-badge.pass { background: #dcfce7; color: #166534; }
  .status-badge.warning { background: #fef3c7; color: #92400e; }
  .status-badge.reject { background: #fee2e2; color: #991b1b; }
  .status-badge.na { background: #f1f5f9; color: #64748b; }
  .chart-card-stats { display: flex; gap: 0.75rem; padding: 0.5rem 1rem; background: #f8fafc; font-size: 0.7rem; color: var(--text-muted); flex-wrap: wrap; }
  .stat-item { display: flex; align-items: center; gap: 3px; }
  .stat-item strong { color: var(--text-primary); }
  .chart-card-body { padding: 1rem; min-height: 160px; }

  /* Modal */
  .chart-modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(15, 23, 42, 0.7);
    backdrop-filter: blur(8px);
    z-index: 9999;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }
  .chart-modal-overlay.active { display: flex; }
  .chart-modal {
    background: #fff;
    border-radius: 24px;
    width: 100%;
    max-width: 1000px;
    max-height: 90vh;
    overflow: auto;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  }
  .chart-modal-header {
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #f8fafc, #f1f5f9);
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .chart-modal-title { font-size: 1.25rem; font-weight: 700; display: flex; align-items: center; gap: 12px; }
  .chart-modal-title .code { background: linear-gradient(135deg, #7c3aed, #3b82f6); color: #fff; padding: 6px 16px; border-radius: 8px; font-size: 0.9rem; }
  .chart-modal-close {
    width: 40px; height: 40px;
    border-radius: 50%;
    border: none;
    background: #f1f5f9;
    color: #64748b;
    cursor: pointer;
    font-size: 1.25rem;
    transition: all 0.2s ease;
  }
  .chart-modal-close:hover { background: #ef4444; color: #fff; }
  .chart-modal-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 1rem;
    padding: 1rem 1.5rem;
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
  }
  .modal-stat { background: #fff; border-radius: 12px; padding: 0.75rem; border: 1px solid #e2e8f0; text-align: center; }
  .modal-stat-label { font-size: 0.7rem; color: var(--text-muted); }
  .modal-stat-value { font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }
  .modal-stat-value.pass { color: #16a34a; }
  .modal-stat-value.warning { color: #b45309; }
  .modal-stat-value.reject { color: #dc2626; }
  .chart-modal-body { padding: 1.5rem; }
  .chart-modal-body canvas { height: 300px !important; }
  .data-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin-top: 1rem; }
  .data-table th, .data-table td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #e2e8f0; }
  .data-table th { background: #f8fafc; font-weight: 600; color: var(--text-muted); position: sticky; top: 0; }
  .data-table tbody tr:hover { background: #f8fafc; }
  .value-ok { color: #16a34a; }
  .value-warn { color: #b45309; }
  .value-bad { color: #dc2626; }
  .badge-retest { background: #dbeafe; color: #1d4ed8; font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; }
  .badge-rejected { background: #f3f4f6; color: #6b7280; font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; }

  .empty-state { text-align: center; padding: 4rem 2rem; }
  .empty-state i { font-size: 4rem; color: #cbd5e1; margin-bottom: 1rem; }
  .loading-state { text-align: center; padding: 3rem; }
  .loading-state .spinner-border { width: 3rem; height: 3rem; color: var(--accent-purple); }

  @media (max-width: 768px) {
    .qc-dashboard { padding: 1rem; }
    .qc-header { flex-direction: column; padding: 1rem; }
    .charts-grid { grid-template-columns: 1fr; }
    .summary-grid { grid-template-columns: repeat(3, 1fr); }
  }
</style>

<div class="qc-dashboard">
  <div class="qc-header">
    <div>
      <h1><i class="bi bi-graph-up-arrow me-2"></i>QC Control Charts</h1>
      <div class="subtitle">ISO 17025 - Levey-Jennings Dashboard</div>
    </div>
    <div class="filter-group">
      <button class="filter-btn active" data-period="all">Бүгд</button>
      <button class="filter-btn" data-period="today">Өнөөдөр</button>
      <button class="filter-btn" data-period="7d">7 хоног</button>
      <button class="filter-btn" data-period="30d">30 хоног</button>
      <button class="filter-btn" data-period="quarter">Улирал</button>
    </div>
    <button class="btn-refresh" onclick="location.reload()"><i class="bi bi-arrow-clockwise"></i></button>
  </div>

  <div class="summary-grid">
    <div class="summary-card total"><div class="summary-label">Нийт</div><div class="summary-value" id="total-count">-</div></div>
    <div class="summary-card pass"><div class="summary-label">OK</div><div class="summary-value" id="pass-count">-</div></div>
    <div class="summary-card warning"><div class="summary-label">Анхааруулга</div><div class="summary-value" id="warning-count">-</div></div>
    <div class="summary-card fail"><div class="summary-label">Хэтэрсэн</div><div class="summary-value" id="fail-count">-</div></div>
    <div class="summary-card retest"><div class="summary-label">Давтан</div><div class="summary-value" id="retest-count">-</div></div>
    <div class="summary-card rejected"><div class="summary-label">Татгалзсан</div><div class="summary-value" id="rejected-count">-</div></div>
  </div>

  <div id="chartsContainer"><div class="loading-state"><div class="spinner-border"></div><div class="mt-3 text-muted">Ачаалж байна...</div></div></div>

  <!-- Modal -->
  <div class="chart-modal-overlay" id="chartModal">
    <div class="chart-modal">
      <div class="chart-modal-header">
        <div class="chart-modal-title"><span class="code" id="modalCode">-</span><span id="modalStandard">-</span></div>
        <button class="chart-modal-close" onclick="closeModal()"><i class="bi bi-x"></i></button>
      </div>
      <div class="chart-modal-stats">
        <div class="modal-stat"><div class="modal-stat-label">Статус</div><div class="modal-stat-value" id="modalStatus">-</div></div>
        <div class="modal-stat"><div class="modal-stat-label">Target</div><div class="modal-stat-value" id="modalTarget">-</div></div>
        <div class="modal-stat"><div class="modal-stat-label">SD</div><div class="modal-stat-value" id="modalSD">-</div></div>
        <div class="modal-stat"><div class="modal-stat-label">UCL</div><div class="modal-stat-value" id="modalUCL">-</div></div>
        <div class="modal-stat"><div class="modal-stat-label">LCL</div><div class="modal-stat-value" id="modalLCL">-</div></div>
        <div class="modal-stat"><div class="modal-stat-label">Нийт (n)</div><div class="modal-stat-value" id="modalCount">-</div></div>
      </div>
      <div class="chart-modal-body">
        <canvas id="modalChart"></canvas>
        <h6 style="font-weight:700;margin:1.5rem 0 0.75rem"><i class="bi bi-table me-2"></i>Хэмжилтийн өгөгдөл</h6>
        <div style="max-height:300px;overflow:auto">
          <table class="data-table">
            <thead><tr><th>#</th><th>Огноо</th><th>Дээж</th><th>Утга</th><th>Статус</th><th>Тэмдэглэл</th></tr></thead>
            <tbody id="modalDataBody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
<script>
let currentPeriod = 'all';
let allAnalyses = [];
let chartInstances = {};
let modalChart = null;

document.addEventListener('DOMContentLoaded', () => {
  loadAllCharts();

  // Filter buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentPeriod = btn.dataset.period;
      loadAllCharts();
    });
  });
});

async function loadAllCharts() {
  const container = document.getElementById('chartsContainer');
  container.innerHTML = '<div class="loading-state"><div class="spinner-border"></div><div class="mt-3 text-muted">Ачаалж байна...</div></div>';

  try {
    const resp = await fetch("{{ url_for('quality.api_westgard_summary') }}");
    const data = await resp.json();

    if (!data.qc_samples || data.qc_samples.length === 0) {
      container.innerHTML = '<div class="empty-state"><i class="bi bi-inbox"></i><h5>CM/GBW дээжний үр дүн олдсонгүй</h5></div>';
      return;
    }

    allAnalyses = data.qc_samples;

    // Group by standard
    const byStandard = {};
    data.qc_samples.forEach(item => {
      if (!byStandard[item.standard_name]) byStandard[item.standard_name] = { qc_type: item.qc_type, analyses: [] };
      byStandard[item.standard_name].analyses.push(item);
    });

    container.innerHTML = '<div class="standards-container"></div>';
    const sc = container.querySelector('.standards-container');

    // Reset summary counts
    let totalCount = 0, okCount = 0, warnCount = 0, outCount = 0, retestCount = 0, rejectedCount = 0;

    for (const sn of Object.keys(byStandard).sort()) {
      const sd = byStandard[sn];
      const isGbw = sd.qc_type === 'GBW';

      const sec = document.createElement('div');
      sec.className = 'standard-section';
      sec.innerHTML = `
        <div class="standard-header ${isGbw ? 'gbw' : 'cm'}">
          <div class="standard-title">
            <i class="bi ${isGbw ? 'bi-award-fill' : 'bi-box-seam-fill'}"></i>
            ${sn}
            <small style="opacity:0.8;font-weight:normal;margin-left:6px">${isGbw ? 'CRM' : 'CM'}</small>
          </div>
          <span class="standard-badge">${sd.analyses.length} шинжилгээ</span>
        </div>
        <div class="chart-legend">
          <div class="legend-item"><div class="legend-dot ok"></div>OK (±1SD)</div>
          <div class="legend-item"><div class="legend-dot warning"></div>Анхааруулга (±2SD)</div>
          <div class="legend-item"><div class="legend-dot out"></div>Хэтэрсэн (>±2SD)</div>
          <div class="legend-item"><div class="legend-dot retest"></div>Давтан</div>
          <div class="legend-item"><div class="legend-line target"></div>Target</div>
          <div class="legend-item"><div class="legend-line sd2"></div>±2SD</div>
        </div>
        <div class="charts-grid"></div>
      `;

      const cg = sec.querySelector('.charts-grid');
      sd.analyses.sort((a, b) => a.analysis_code.localeCompare(b.analysis_code));

      for (const an of sd.analyses) {
        const cid = 'chart_' + sn.replace(/[^a-zA-Z0-9]/g, '_') + '_' + an.analysis_code;
        const sc2 = an.status === 'pass' ? 'pass' : an.status === 'warning' ? 'warning' : an.status === 'reject' ? 'reject' : 'na';
        const st = an.status === 'pass' ? 'Pass' : an.status === 'warning' ? 'Warning' : an.status === 'reject' ? 'Reject' : 'N/A';

        const cd = document.createElement('div');
        cd.className = 'chart-card';
        cd.onclick = () => openChartModal(sn, sd.qc_type, an);
        cd.innerHTML = `
          <div class="chart-card-header">
            <div class="chart-card-title"><span class="code">${an.analysis_code}</span></div>
            <span class="status-badge ${sc2}">${st}</span>
          </div>
          <div class="chart-card-stats">
            <div class="stat-item"><i class="bi bi-bullseye"></i> Target: <strong>${an.target || '-'}</strong></div>
            <div class="stat-item"><i class="bi bi-arrows-expand"></i> SD: <strong>${an.sd || '-'}</strong></div>
            <div class="stat-item"><i class="bi bi-hash"></i> n=<strong>${an.count}</strong></div>
          </div>
          <div class="chart-card-body"><canvas id="${cid}" height="140"></canvas></div>
        `;
        cg.appendChild(cd);
      }

      sc.appendChild(sec);

      // Load chart data for each analysis
      for (const an of sd.analyses) {
        const stats = await loadChartData(sn, sd.qc_type, an);
        if (stats) {
          totalCount += stats.total;
          okCount += stats.ok;
          warnCount += stats.warning;
          outCount += stats.out;
          retestCount += stats.retest;
          rejectedCount += stats.rejected;
        }
      }
    }

    // Update summary
    document.getElementById('total-count').textContent = totalCount;
    document.getElementById('pass-count').textContent = okCount;
    document.getElementById('warning-count').textContent = warnCount;
    document.getElementById('fail-count').textContent = outCount;
    document.getElementById('retest-count').textContent = retestCount;
    document.getElementById('rejected-count').textContent = rejectedCount;

  } catch (err) {
    container.innerHTML = '<div class="empty-state"><i class="bi bi-exclamation-triangle"></i><h5>Алдаа</h5><p>' + err.message + '</p></div>';
  }
}

async function loadChartData(sn, qt, an) {
  try {
    const resp = await fetch('/quality/api/westgard_detail/' + encodeURIComponent(qt) + '/' + encodeURIComponent(an.analysis_code) + '?period=' + currentPeriod);
    const data = await resp.json();

    const cid = 'chart_' + sn.replace(/[^a-zA-Z0-9]/g, '_') + '_' + an.analysis_code;
    const ctx = document.getElementById(cid);

    if (!ctx || !data.data_points || data.data_points.length < 1) {
      if (ctx) ctx.parentElement.innerHTML = '<div class="text-muted text-center py-4"><i class="bi bi-graph-down"></i> Өгөгдөл байхгүй</div>';
      return null;
    }

    // Filter by standard name
    const pts = data.data_points
      .filter(p => (p.sample_code || '').toUpperCase().startsWith(sn.toUpperCase()))
      .sort((a, b) => new Date(a.date) - new Date(b.date));

    if (pts.length < 1) {
      ctx.parentElement.innerHTML = '<div class="text-muted text-center py-4"><i class="bi bi-graph-down"></i> Өгөгдөл байхгүй</div>';
      return null;
    }

    const labels = pts.map(p => p.date ? new Date(p.date).toLocaleDateString('mn-MN', {month:'numeric', day:'numeric'}) : '');
    const values = pts.map(p => p.value);
    const target = data.target, sd = data.sd;
    const ucl = target + 2*sd, lcl = target - 2*sd;

    // Point colors based on status and retest
    const pointColors = pts.map(p => {
      if (p.is_retest) return '#3b82f6';  // Blue for retest
      if (p.point_status === 'out_of_control') return '#ef4444';  // Red
      if (p.point_status === 'warning') return '#f59e0b';  // Orange
      return '#22c55e';  // Green
    });

    const pointBorders = pts.map(p => p.is_retest ? '#1d4ed8' : pointColors[pts.indexOf(p)]);
    const pointSizes = pts.map(p => p.is_retest ? 7 : 5);

    // Destroy old chart if exists
    if (chartInstances[cid]) chartInstances[cid].destroy();

    chartInstances[cid] = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: 'Хэмжсэн', data: values, borderColor: '#3b82f6', tension: 0.2, pointRadius: pointSizes, pointBackgroundColor: pointColors, pointBorderColor: pointBorders, pointBorderWidth: 2, fill: false, order: 1 },
          { label: 'Target', data: Array(labels.length).fill(target), borderColor: '#1e293b', borderWidth: 2, pointRadius: 0, order: 2 },
          { label: '+2SD', data: Array(labels.length).fill(ucl), borderColor: '#ef4444', borderWidth: 1.5, pointRadius: 0, order: 3 },
          { label: '-2SD', data: Array(labels.length).fill(lcl), borderColor: '#ef4444', borderWidth: 1.5, pointRadius: 0, order: 4 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(15,23,42,0.95)',
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              title: (items) => {
                const idx = items[0].dataIndex;
                const p = pts[idx];
                return p.date ? new Date(p.date).toLocaleString('mn-MN') : '';
              },
              label: (item) => {
                if (item.datasetIndex !== 0) return item.dataset.label + ': ' + item.raw.toFixed(4);
                const p = pts[item.dataIndex];
                const lines = [
                  'Утга: ' + p.value.toFixed(4),
                  'Дээж: ' + (p.sample_code || '-'),
                  'Оператор: ' + (p.operator || '-')
                ];
                if (p.is_retest) lines.push('📌 Давтан шинжилгээ');
                if (p.result_status === 'rejected') lines.push('❌ Татгалзсан');
                if (p.point_status === 'out_of_control') lines.push('⚠️ ±2SD хэтэрсэн');
                else if (p.point_status === 'warning') lines.push('⚡ ±1SD хэтэрсэн');
                return lines;
              }
            }
          }
        },
        scales: {
          y: { beginAtZero: false, grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { font: { size: 9 } } },
          x: { grid: { display: false }, ticks: { font: { size: 9 }, maxRotation: 45 } }
        }
      }
    });

    // Return stats
    return {
      total: pts.length,
      ok: pts.filter(p => p.point_status === 'ok').length,
      warning: pts.filter(p => p.point_status === 'warning').length,
      out: pts.filter(p => p.point_status === 'out_of_control').length,
      retest: pts.filter(p => p.is_retest).length,
      rejected: pts.filter(p => p.result_status === 'rejected').length
    };

  } catch (err) {
    console.error('Chart error:', err);
    return null;
  }
}

function openChartModal(standardName, qcType, analysis) {
  const modal = document.getElementById('chartModal');
  document.getElementById('modalCode').textContent = analysis.analysis_code;
  document.getElementById('modalStandard').textContent = standardName + ' (' + qcType + ')';
  document.getElementById('modalTarget').textContent = analysis.target || '-';
  document.getElementById('modalSD').textContent = analysis.sd || '-';

  modal.classList.add('active');
  document.body.style.overflow = 'hidden';

  loadModalChart(standardName, qcType, analysis.analysis_code);
}

function closeModal() {
  document.getElementById('chartModal').classList.remove('active');
  document.body.style.overflow = '';
  if (modalChart) { modalChart.destroy(); modalChart = null; }
}

document.getElementById('chartModal').addEventListener('click', function(e) { if (e.target === this) closeModal(); });
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeModal(); });

async function loadModalChart(standardName, qcType, analysisCode) {
  try {
    const resp = await fetch('/quality/api/westgard_detail/' + encodeURIComponent(qcType) + '/' + encodeURIComponent(analysisCode) + '?period=' + currentPeriod);
    const data = await resp.json();

    document.getElementById('modalUCL').textContent = data.ucl ? data.ucl.toFixed(4) : '-';
    document.getElementById('modalLCL').textContent = data.lcl ? data.lcl.toFixed(4) : '-';
    document.getElementById('modalCount').textContent = data.count || 0;

    const statusEl = document.getElementById('modalStatus');
    const st = data.qc_status?.status || 'N/A';
    statusEl.textContent = st.toUpperCase();
    statusEl.className = 'modal-stat-value ' + (st === 'pass' ? 'pass' : st === 'warning' ? 'warning' : st === 'reject' ? 'reject' : '');

    const tbody = document.getElementById('modalDataBody');
    tbody.innerHTML = '';

    if (data.data_points) {
      const pts = data.data_points
        .filter(p => (p.sample_code || '').toUpperCase().startsWith(standardName.toUpperCase()))
        .sort((a, b) => new Date(b.date) - new Date(a.date));

      pts.forEach((p, i) => {
        let statusClass = 'value-ok', statusText = 'OK';
        if (p.point_status === 'out_of_control') { statusClass = 'value-bad'; statusText = 'Хэтэрсэн'; }
        else if (p.point_status === 'warning') { statusClass = 'value-warn'; statusText = 'Анхааруулга'; }

        let notes = '';
        if (p.is_retest) notes += '<span class="badge-retest">Давтан</span> ';
        if (p.result_status === 'rejected') notes += '<span class="badge-rejected">Татгалзсан</span>';

        const date = p.date ? new Date(p.date).toLocaleString('mn-MN') : '-';
        tbody.innerHTML += '<tr><td>' + (i+1) + '</td><td>' + date + '</td><td style="font-size:0.75rem">' + (p.sample_code || '-') + '</td><td class="' + statusClass + '" style="font-weight:600">' + p.value.toFixed(4) + '</td><td class="' + statusClass + '">' + statusText + '</td><td>' + notes + '</td></tr>';
      });

      // Draw chart
      const ctx = document.getElementById('modalChart');
      if (modalChart) modalChart.destroy();

      const chartPts = pts.sort((a, b) => new Date(a.date) - new Date(b.date));
      if (chartPts.length >= 1) {
        const labels = chartPts.map(p => p.date ? new Date(p.date).toLocaleString('mn-MN', {month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit'}) : '');
        const values = chartPts.map(p => p.value);
        const target = data.target, sd = data.sd;
        const ucl = target + 2*sd, lcl = target - 2*sd, ucl3 = target + 3*sd, lcl3 = target - 3*sd, usl1 = target + sd, lsl1 = target - sd;

        const pc = chartPts.map(p => {
          if (p.is_retest) return '#3b82f6';
          if (p.point_status === 'out_of_control') return '#ef4444';
          if (p.point_status === 'warning') return '#f59e0b';
          return '#22c55e';
        });

        modalChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels,
            datasets: [
              { label: 'Хэмжсэн', data: values, borderColor: '#3b82f6', tension: 0.2, pointRadius: 6, pointBackgroundColor: pc, pointBorderColor: pc, fill: false, order: 1 },
              { label: 'Target', data: Array(labels.length).fill(target), borderColor: '#1e293b', borderWidth: 2, pointRadius: 0, order: 2 },
              { label: '+1SD', data: Array(labels.length).fill(usl1), borderColor: '#22c55e', borderWidth: 1, borderDash: [4,4], pointRadius: 0, order: 3 },
              { label: '-1SD', data: Array(labels.length).fill(lsl1), borderColor: '#22c55e', borderWidth: 1, borderDash: [4,4], pointRadius: 0, order: 4 },
              { label: '+2SD', data: Array(labels.length).fill(ucl), borderColor: '#ef4444', borderWidth: 2, pointRadius: 0, order: 5 },
              { label: '-2SD', data: Array(labels.length).fill(lcl), borderColor: '#ef4444', borderWidth: 2, pointRadius: 0, order: 6 },
              { label: '+3SD', data: Array(labels.length).fill(ucl3), borderColor: '#9333ea', borderWidth: 1, borderDash: [5,5], pointRadius: 0, order: 7 },
              { label: '-3SD', data: Array(labels.length).fill(lcl3), borderColor: '#9333ea', borderWidth: 1, borderDash: [5,5], pointRadius: 0, order: 8 }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: true, position: 'top', labels: { boxWidth: 12, font: { size: 10 } } },
              tooltip: {
                backgroundColor: 'rgba(15,23,42,0.95)',
                padding: 12,
                callbacks: {
                  label: (item) => {
                    if (item.datasetIndex !== 0) return item.dataset.label + ': ' + item.raw.toFixed(4);
                    const p = chartPts[item.dataIndex];
                    return ['Утга: ' + p.value.toFixed(4), p.is_retest ? '📌 Давтан' : '', p.result_status === 'rejected' ? '❌ Татгалзсан' : ''].filter(Boolean);
                  }
                }
              }
            },
            scales: {
              y: { beginAtZero: false, grid: { color: 'rgba(148,163,184,0.15)' } },
              x: { grid: { display: false }, ticks: { maxRotation: 45 } }
            }
          }
        });
      }
    }
  } catch (err) { console.error('Modal error:', err); }
}
</script>
{% endblock %}
'''

with open(r'D:/coal_lims_project/app/templates/quality/control_charts.html', 'w', encoding='utf-8') as f:
    f.write(template)
print('Template updated successfully!')
