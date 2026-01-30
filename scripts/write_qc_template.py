#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Write QC Control Charts template with card design"""

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
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.4);
    border-radius: 24px;
    padding: 1.25rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 24px rgba(139,92,246,0.1), inset 0 1px 0 rgba(255,255,255,0.6);
  }
  .qc-header h1 {
    font-size: 1.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 50%, #0891b2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
  }
  .qc-header .subtitle { font-size: 0.85rem; color: var(--text-muted); margin-top: 4px; }
  .btn-refresh {
    padding: 10px 20px;
    border-radius: 50px;
    font-weight: 600;
    border: none;
    background: rgba(255,255,255,0.8);
    color: var(--accent-purple);
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .btn-refresh:hover {
    background: var(--accent-purple);
    color: #fff;
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(139,92,246,0.3);
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  .summary-card {
    background: var(--glass-bg);
    backdrop-filter: blur(16px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 1.25rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
    animation: fadeInUp 0.5s ease backwards;
  }
  .summary-card:hover { transform: translateY(-4px); box-shadow: 0 12px 30px rgba(0,0,0,0.1); }
  .summary-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; border-radius: 20px 20px 0 0; }
  .summary-card.total::before { background: linear-gradient(90deg, #3b82f6, #06b6d4); }
  .summary-card.pass::before { background: linear-gradient(90deg, #22c55e, #4ade80); }
  .summary-card.warning::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
  .summary-card.fail::before { background: linear-gradient(90deg, #ef4444, #f87171); }
  .summary-card-inner { display: flex; align-items: center; gap: 12px; }
  .summary-icon { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }
  .summary-card.total .summary-icon { background: linear-gradient(135deg, #dbeafe, #bfdbfe); color: #1d4ed8; }
  .summary-card.pass .summary-icon { background: linear-gradient(135deg, #dcfce7, #bbf7d0); color: #16a34a; }
  .summary-card.warning .summary-icon { background: linear-gradient(135deg, #fef3c7, #fde68a); color: #b45309; }
  .summary-card.fail .summary-icon { background: linear-gradient(135deg, #fee2e2, #fecaca); color: #dc2626; }
  .summary-content { flex: 1; }
  .summary-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }
  .summary-value { font-size: 1.75rem; font-weight: 800; line-height: 1.2; }
  .summary-card.total .summary-value { color: #1d4ed8; }
  .summary-card.pass .summary-value { color: #16a34a; }
  .summary-card.warning .summary-value { color: #b45309; }
  .summary-card.fail .summary-value { color: #dc2626; }

  .standards-container { display: flex; flex-direction: column; gap: 1.5rem; }
  .standard-section { background: var(--glass-bg); backdrop-filter: blur(16px); border: 1px solid var(--glass-border); border-radius: 24px; overflow: hidden; box-shadow: var(--shadow-soft); animation: fadeInUp 0.5s ease 0.3s backwards; }
  .standard-header { padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center; color: #fff; }
  .standard-header.gbw { background: linear-gradient(135deg, #0891b2 0%, #06b6d4 50%, #22d3ee 100%); }
  .standard-header.cm { background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 50%, #a78bfa 100%); }
  .standard-title { font-weight: 700; font-size: 1.1rem; display: flex; align-items: center; gap: 10px; }
  .standard-badge { background: rgba(255,255,255,0.25); padding: 6px 14px; border-radius: 50px; font-size: 0.8rem; font-weight: 600; }
  .chart-legend { display: flex; gap: 1.5rem; padding: 0.75rem 1.5rem; background: rgba(248,250,252,0.8); border-bottom: 1px solid var(--glass-border); flex-wrap: wrap; }
  .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: var(--text-muted); }
  .legend-line { width: 24px; height: 3px; border-radius: 2px; }
  .legend-line.target { background: #1e293b; }
  .legend-line.sd1 { background: #22c55e; }
  .legend-line.sd2 { background: #ef4444; }
  .legend-line.sd3 { background: #9333ea; }

  .charts-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 1rem; padding: 1.25rem; }
  .chart-card { background: #fff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; transition: all 0.3s ease; animation: fadeInUp 0.4s ease backwards; }
  .chart-card:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); border-color: var(--accent-purple); }
  .chart-card-header { padding: 0.75rem 1rem; display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #f8fafc, #f1f5f9); border-bottom: 1px solid #e2e8f0; }
  .chart-card-title { font-weight: 700; font-size: 0.95rem; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }
  .chart-card-title .code { background: linear-gradient(135deg, #7c3aed, #3b82f6); color: #fff; padding: 3px 10px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; }
  .status-badge { padding: 4px 12px; border-radius: 50px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
  .status-badge.pass { background: #dcfce7; color: #166534; }
  .status-badge.warning { background: #fef3c7; color: #92400e; }
  .status-badge.reject { background: #fee2e2; color: #991b1b; }
  .status-badge.na { background: #f1f5f9; color: #64748b; }
  .chart-card-stats { display: flex; gap: 1rem; padding: 0.5rem 1rem; background: #f8fafc; font-size: 0.72rem; color: var(--text-muted); }
  .stat-item { display: flex; align-items: center; gap: 4px; }
  .stat-item strong { color: var(--text-primary); }
  .chart-card-body { padding: 1rem; min-height: 140px; }

  .empty-state { text-align: center; padding: 4rem 2rem; background: var(--glass-bg); backdrop-filter: blur(16px); border-radius: 24px; border: 1px solid var(--glass-border); }
  .empty-state i { font-size: 4rem; color: #cbd5e1; margin-bottom: 1rem; }
  .empty-state h5 { font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.5rem; }
  .empty-state p { color: var(--text-muted); font-size: 0.9rem; }
  .loading-state { text-align: center; padding: 3rem; }
  .loading-state .spinner-border { width: 3rem; height: 3rem; color: var(--accent-purple); }

  @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
  @media (max-width: 768px) { .qc-dashboard { padding: 1rem; } .qc-header { flex-direction: column; gap: 1rem; text-align: center; padding: 1rem; } .qc-header h1 { font-size: 1.3rem; } .charts-grid { grid-template-columns: 1fr; } .summary-grid { grid-template-columns: repeat(2, 1fr); } }
</style>

<div class="qc-dashboard">
  <div class="qc-header">
    <div>
      <h1><i class="bi bi-graph-up-arrow me-2"></i>QC Control Charts</h1>
      <div class="subtitle">ISO 17025 - Levey-Jennings Dashboard</div>
    </div>
    <button class="btn-refresh" onclick="location.reload()"><i class="bi bi-arrow-clockwise"></i> Шинэчлэх</button>
  </div>
  <div class="summary-grid">
    <div class="summary-card total"><div class="summary-card-inner"><div class="summary-icon"><i class="bi bi-stack"></i></div><div class="summary-content"><div class="summary-label">Нийт шинжилгээ</div><div class="summary-value" id="total-count">-</div></div></div></div>
    <div class="summary-card pass"><div class="summary-card-inner"><div class="summary-icon"><i class="bi bi-check-circle-fill"></i></div><div class="summary-content"><div class="summary-label">Pass</div><div class="summary-value" id="pass-count">-</div></div></div></div>
    <div class="summary-card warning"><div class="summary-card-inner"><div class="summary-icon"><i class="bi bi-exclamation-triangle-fill"></i></div><div class="summary-content"><div class="summary-label">Warning</div><div class="summary-value" id="warning-count">-</div></div></div></div>
    <div class="summary-card fail"><div class="summary-card-inner"><div class="summary-icon"><i class="bi bi-x-circle-fill"></i></div><div class="summary-content"><div class="summary-label">Reject</div><div class="summary-value" id="fail-count">-</div></div></div></div>
  </div>
  <div id="chartsContainer"><div class="loading-state"><div class="spinner-border"></div><div class="mt-3 text-muted">Ачаалж байна...</div></div></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', loadAllCharts);

async function loadAllCharts() {
  const container = document.getElementById('chartsContainer');
  try {
    const resp = await fetch("{{ url_for('quality.api_westgard_summary') }}");
    const data = await resp.json();
    if (!data.qc_samples || data.qc_samples.length === 0) {
      container.innerHTML = '<div class="empty-state"><i class="bi bi-inbox"></i><h5>CM/GBW дээжний үр дүн олдсонгүй</h5></div>';
      return;
    }
    let passCount = 0, warningCount = 0, failCount = 0;
    data.qc_samples.forEach(item => {
      if (item.status === 'pass') passCount++;
      else if (item.status === 'warning') warningCount++;
      else if (item.status === 'reject') failCount++;
    });
    document.getElementById('total-count').textContent = data.qc_samples.length;
    document.getElementById('pass-count').textContent = passCount;
    document.getElementById('warning-count').textContent = warningCount;
    document.getElementById('fail-count').textContent = failCount;
    const byStandard = {};
    data.qc_samples.forEach(item => {
      if (!byStandard[item.standard_name]) byStandard[item.standard_name] = { qc_type: item.qc_type, analyses: [] };
      byStandard[item.standard_name].analyses.push(item);
    });
    container.innerHTML = '<div class="standards-container"></div>';
    const sc = container.querySelector('.standards-container');
    for (const sn of Object.keys(byStandard).sort()) {
      const sd = byStandard[sn];
      const isGbw = sd.qc_type === 'GBW';
      const sec = document.createElement('div');
      sec.className = 'standard-section';
      sec.innerHTML = '<div class="standard-header ' + (isGbw ? 'gbw' : 'cm') + '"><div class="standard-title"><i class="bi ' + (isGbw ? 'bi-award-fill' : 'bi-box-seam-fill') + '"></i>' + sn + '<small style="opacity:0.8;font-weight:normal;margin-left:6px">' + (isGbw ? 'CRM' : 'CM') + '</small></div><span class="standard-badge">' + sd.analyses.length + ' шинжилгээ</span></div><div class="chart-legend"><div class="legend-item"><div class="legend-line target"></div>Target</div><div class="legend-item"><div class="legend-line sd1"></div>±1SD</div><div class="legend-item"><div class="legend-line sd2"></div>±2SD</div><div class="legend-item"><div class="legend-line sd3"></div>±3SD</div></div><div class="charts-grid"></div>';
      const cg = sec.querySelector('.charts-grid');
      sd.analyses.sort((a, b) => a.analysis_code.localeCompare(b.analysis_code));
      sd.analyses.forEach((an, idx) => {
        const sc2 = an.status === 'pass' ? 'pass' : an.status === 'warning' ? 'warning' : an.status === 'reject' ? 'reject' : 'na';
        const st = an.status === 'pass' ? 'Pass' : an.status === 'warning' ? 'Warning' : an.status === 'reject' ? 'Reject' : 'N/A';
        const cid = 'chart_' + sn.replace(/[^a-zA-Z0-9]/g, '_') + '_' + an.analysis_code;
        const cd = document.createElement('div');
        cd.className = 'chart-card';
        cd.style.animationDelay = (idx * 0.05) + 's';
        cd.innerHTML = '<div class="chart-card-header"><div class="chart-card-title"><span class="code">' + an.analysis_code + '</span></div><span class="status-badge ' + sc2 + '">' + st + '</span></div><div class="chart-card-stats"><div class="stat-item"><i class="bi bi-bullseye"></i> Target: <strong>' + (an.target || '-') + '</strong></div><div class="stat-item"><i class="bi bi-arrows-expand"></i> SD: <strong>' + (an.sd || '-') + '</strong></div><div class="stat-item"><i class="bi bi-hash"></i> n=<strong>' + an.count + '</strong></div></div><div class="chart-card-body"><canvas id="' + cid + '" height="120"></canvas></div>';
        cg.appendChild(cd);
      });
      sc.appendChild(sec);
      for (const an of sd.analyses) await loadChartData(sn, sd.qc_type, an);
    }
  } catch (err) { container.innerHTML = '<div class="empty-state"><i class="bi bi-exclamation-triangle"></i><h5>Алдаа</h5><p>' + err.message + '</p></div>'; }
}

async function loadChartData(sn, qt, an) {
  try {
    const resp = await fetch('/quality/api/westgard_detail/' + encodeURIComponent(qt) + '/' + encodeURIComponent(an.analysis_code));
    const data = await resp.json();
    const cid = 'chart_' + sn.replace(/[^a-zA-Z0-9]/g, '_') + '_' + an.analysis_code;
    const ctx = document.getElementById(cid);
    if (!ctx || !data.data_points || data.data_points.length < 2) return;
    const pts = data.data_points.filter(p => (p.sample_code || '').toUpperCase().startsWith(sn.toUpperCase())).sort((a, b) => new Date(a.date) - new Date(b.date)).slice(-30);
    if (pts.length < 2) { ctx.parentElement.innerHTML = '<div class="text-muted text-center py-4"><i class="bi bi-graph-down"></i> Хангалттай өгөгдөл байхгүй</div>'; return; }
    const labels = pts.map(p => p.date ? new Date(p.date).getMonth()+1 + '/' + new Date(p.date).getDate() : '');
    const values = pts.map(p => p.value);
    const target = data.target, sd = data.sd;
    const ucl = target + 2*sd, lcl = target - 2*sd, ucl3 = target + 3*sd, lcl3 = target - 3*sd, usl1 = target + sd, lsl1 = target - sd;
    const pc = values.map(v => { if (v > ucl || v < lcl) return '#ef4444'; if (v > usl1 || v < lsl1) return '#f59e0b'; return '#22c55e'; });
    new Chart(ctx, {
      type: 'line',
      data: { labels, datasets: [
        { label: 'Хэмжсэн', data: values, borderColor: '#3b82f6', tension: 0.2, pointRadius: 5, pointBackgroundColor: pc, pointBorderColor: pc, fill: false, order: 1 },
        { label: 'Target', data: Array(labels.length).fill(target), borderColor: '#1e293b', borderWidth: 2, pointRadius: 0, order: 2 },
        { label: '+1SD', data: Array(labels.length).fill(usl1), borderColor: '#22c55e', borderWidth: 1, borderDash: [4,4], pointRadius: 0, order: 3 },
        { label: '-1SD', data: Array(labels.length).fill(lsl1), borderColor: '#22c55e', borderWidth: 1, borderDash: [4,4], pointRadius: 0, order: 4 },
        { label: '+2SD', data: Array(labels.length).fill(ucl), borderColor: '#ef4444', borderWidth: 2, pointRadius: 0, order: 5 },
        { label: '-2SD', data: Array(labels.length).fill(lcl), borderColor: '#ef4444', borderWidth: 2, pointRadius: 0, order: 6 },
        { label: '+3SD', data: Array(labels.length).fill(ucl3), borderColor: '#9333ea', borderWidth: 1, borderDash: [5,5], pointRadius: 0, order: 7 },
        { label: '-3SD', data: Array(labels.length).fill(lcl3), borderColor: '#9333ea', borderWidth: 1, borderDash: [5,5], pointRadius: 0, order: 8 }
      ]},
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { backgroundColor: 'rgba(15,23,42,0.9)', padding: 12, cornerRadius: 8 } }, scales: { y: { beginAtZero: false, grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { font: { size: 10 } } }, x: { grid: { display: false }, ticks: { font: { size: 10 } } } } }
    });
  } catch (err) { console.error('Chart error:', err); }
}
</script>
{% endblock %}'''

if __name__ == '__main__':
    with open('D:/coal_lims_project/app/templates/quality/control_charts.html', 'w', encoding='utf-8') as f:
        f.write(template)
    print('Template written successfully!')
