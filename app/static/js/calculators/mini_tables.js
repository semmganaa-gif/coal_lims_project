// app/static/js/mini_tables.js
// Ахлахын самбар + бусад газар ашиглах мини хүснэгтүүд

(function () {
  'use strict';

  // --------------------------------------------------
  // Туслах функцууд
  // --------------------------------------------------
  function esc(v) {
    if (v === null || v === undefined) return '-';
    return String(v)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function fmt(v, digits) {
    if (v === null || v === undefined || v === '') return '-';
    const n = Number(v);
    if (!isFinite(n)) return esc(v);
    return n.toFixed(digits);
  }

  function getP(data) {
    data = data || {};
    return {
      p1: data.p1 || {},
      p2: data.p2 || {}
    };
  }

  function renderDefaultRaw(rawData) {
    try {
      return '<pre style="font-size:0.8em;max-width:480px;margin-bottom:0;">' +
        esc(JSON.stringify(rawData || {}, null, 2)) +
        '</pre>';
    } catch (e) {
      return '<pre style="font-size:0.8em;max-width:480px;margin-bottom:0;">(хоосон)</pre>';
    }
  }

  // --------------------------------------------------
  // Aad – үнслэг
  // --------------------------------------------------
  function renderAad(data) {
    const p = getP(data);
    let html =
      '<table class="table table-sm table-bordered mb-0" ' +
      'style="font-size:0.8em;width:100%;margin:0;">' +
      '<thead class="table-light">' +
      '<tr>' +
      '<th>Тигель №</th>' +
      '<th>Хоосон тигель (m1)</th>' +
      '<th>Дээжийн жин (m2)</th>' +
      '<th>Үнстэй тигель (m3)</th>' +
      '<th>Үр дүн</th>' +
      '</tr></thead><tbody>';

    html += '<tr>' +
      '<td>' + esc(p.p1.num || p.p1.dish_num || '-') + '</td>' +
      '<td>' + fmt(p.p1.m1, 4) + '</td>' +
      '<td>' + fmt(p.p1.m2, 4) + '</td>' +
      '<td>' + fmt(p.p1.m3, 4) + '</td>' +
      '<td>' + fmt(p.p1.result, 2) + '</td>' +
      '</tr>';

    html += '<tr>' +
      '<td>' + esc(p.p2.num || p.p2.dish_num || '-') + '</td>' +
      '<td>' + fmt(p.p2.m1, 4) + '</td>' +
      '<td>' + fmt(p.p2.m2, 4) + '</td>' +
      '<td>' + fmt(p.p2.m3, 4) + '</td>' +
      '<td>' + fmt(p.p2.result, 2) + '</td>' +
      '</tr>';

    html += '</tbody></table>';
    return html;
  }

  // --------------------------------------------------
  // Mad – дотоод чийг
  // --------------------------------------------------
  function renderMad(data) {
    const p = getP(data);
    let html =
      '<table class="table table-sm table-bordered mb-0" ' +
      'style="font-size:0.8em;width:100%;margin:0;">' +
      '<thead class="table-light">' +
      '<tr>' +
      '<th>Бюкс №</th>' +
      '<th>Хоосон бюкс (m1)</th>' +
      '<th>Дээжтэй бюкс (m2)</th>' +
      '<th>Хатаасан бюкс (m3)</th>' +
      '<th>Үр дүн</th>' +
      '</tr></thead><tbody>';

    html += '<tr>' +
      '<td>' + esc(p.p1.num || p.p1.dish_num || '-') + '</td>' +
      '<td>' + fmt(p.p1.m1, 4) + '</td>' +
      '<td>' + fmt(p.p1.m2, 4) + '</td>' +
      '<td>' + fmt(p.p1.m3, 4) + '</td>' +
      '<td>' + fmt(p.p1.result, 2) + '</td>' +
      '</tr>';

    html += '<tr>' +
      '<td>' + esc(p.p2.num || p.p2.dish_num || '-') + '</td>' +
      '<td>' + fmt(p.p2.m1, 4) + '</td>' +
      '<td>' + fmt(p.p2.m2, 4) + '</td>' +
      '<td>' + fmt(p.p2.m3, 4) + '</td>' +
      '<td>' + fmt(p.p2.result, 2) + '</td>' +
      '</tr>';

    html += '</tbody></table>';
    return html;
  }

  // --------------------------------------------------
  // Vad – дэгдэмхий бодис
  // --------------------------------------------------
  function renderVad(data) {
    const p = getP(data);
    let html =
      '<table class="table table-sm table-bordered mb-0" ' +
      'style="font-size:0.8em;width:100%;margin:0;">' +
      '<thead class="table-light">' +
      '<tr>' +
      '<th>Тигель №</th>' +
      '<th>Хоосон тигель (m1)</th>' +
      '<th>Дээжтэй тигель (m2)</th>' +
      '<th>Үлдэгдэлтэй тигель (m3)</th>' +
      '<th>Үр дүн</th>' +
      '</tr></thead><tbody>';

    html += '<tr>' +
      '<td>' + esc(p.p1.num || p.p1.dish_num || '-') + '</td>' +
      '<td>' + fmt(p.p1.m1, 4) + '</td>' +
      '<td>' + fmt(p.p1.m2, 4) + '</td>' +
      '<td>' + fmt(p.p1.m3, 4) + '</td>' +
      '<td>' + fmt(p.p1.result, 2) + '</td>' +
      '</tr>';

    html += '<tr>' +
      '<td>' + esc(p.p2.num || p.p2.dish_num || '-') + '</td>' +
      '<td>' + fmt(p.p2.m1, 4) + '</td>' +
      '<td>' + fmt(p.p2.m2, 4) + '</td>' +
      '<td>' + fmt(p.p2.m3, 4) + '</td>' +
      '<td>' + fmt(p.p2.result, 2) + '</td>' +
      '</tr>';

    html += '</tbody></table>';
    return html;
  }

  // --------------------------------------------------
  // MT – нийт чийг
  // --------------------------------------------------
  function renderMt(data) {
    const p = getP(data);
    let html =
      '<table class="table table-sm table-bordered mb-0" ' +
      'style="font-size:0.8em;width:100%;margin:0;">' +
      '<thead class="table-light">' +
      '<tr>' +
      '<th>Бокс №</th>' +
      '<th>m1 (хоосон)</th>' +
      '<th>m2 (дээжтэй)</th>' +
      '<th>m3 (хатаасан)</th>' +
      '<th>Үр дүн</th>' +
      '</tr></thead><tbody>';

    html += '<tr>' +
      '<td>' + esc(p.p1.num || p.p1.box_num || '-') + '</td>' +
      '<td>' + fmt(p.p1.m1, 4) + '</td>' +
      '<td>' + fmt(p.p1.m2, 4) + '</td>' +
      '<td>' + fmt(p.p1.m3, 4) + '</td>' +
      '<td>' + fmt(p.p1.result, 2) + '</td>' +
      '</tr>';

    html += '<tr>' +
      '<td>' + esc(p.p2.num || p.p2.box_num || '-') + '</td>' +
      '<td>' + fmt(p.p2.m1, 4) + '</td>' +
      '<td>' + fmt(p.p2.m2, 4) + '</td>' +
      '<td>' + fmt(p.p2.m3, 4) + '</td>' +
      '<td>' + fmt(p.p2.result, 2) + '</td>' +
      '</tr>';

    html += '</tbody></table>';
    return html;
  }

  // --------------------------------------------------
  // CSN – хөөлтийн зэрэг
  // --------------------------------------------------
  function renderCsn(data) {
    data = data || {};
    let html =
      '<table class="table table-sm table-bordered mb-0" ' +
      'style="font-size:0.8em;width:100%;margin:0;">' +
      '<thead class="table-light">' +
      '<tr>' +
      '<th class="text-center">v1</th>' +
      '<th class="text-center">v2</th>' +
      '<th class="text-center">v3</th>' +
      '<th class="text-center">v4</th>' +
      '<th class="text-center">v5</th>' +
      '</tr></thead><tbody>';

    html += '<tr>' +
      '<td class="text-center">' + esc(data.v1 || '-') + '</td>' +
      '<td class="text-center">' + esc(data.v2 || '-') + '</td>' +
      '<td class="text-center">' + esc(data.v3 || '-') + '</td>' +
      '<td class="text-center">' + esc(data.v4 || '-') + '</td>' +
      '<td class="text-center">' + esc(data.v5 || '-') + '</td>' +
      '</tr>';

    html += '</tbody></table>';
    return html;
  }

  // --------------------------------------------------
  // Gi – барьцалдах чадвар
  // --------------------------------------------------
  function renderGi(data) {
    const p = getP(data);
    let html =
      '<table class="table table-sm table-bordered mb-0" ' +
      'style="font-size:0.8em;width:100%;margin:0;">' +
      '<thead class="table-light">' +
      '<tr>' +
      '<th>Тигель №</th>' +
      '<th>m1</th>' +
      '<th>m2</th>' +
      '<th>m3</th>' +
      '<th>Үр дүн</th>' +
      '</tr></thead><tbody>';

    html += '<tr>' +
      '<td>' + esc(p.p1.num || '-') + '</td>' +
      '<td>' + fmt(p.p1.m1, 4) + '</td>' +
      '<td>' + fmt(p.p1.m2, 4) + '</td>' +
      '<td>' + fmt(p.p1.m3, 4) + '</td>' +
      '<td>' + esc(p.p1.result != null ? p.p1.result : '-') + '</td>' +
      '</tr>';

    html += '<tr>' +
      '<td>' + esc(p.p2.num || '-') + '</td>' +
      '<td>' + fmt(p.p2.m1, 4) + '</td>' +
      '<td>' + fmt(p.p2.m2, 4) + '</td>' +
      '<td>' + fmt(p.p2.m3, 4) + '</td>' +
      '<td>' + esc(p.p2.result != null ? p.p2.result : '-') + '</td>' +
      '</tr>';

    html += '</tbody></table>';
    return html;
  }

  // --------------------------------------------------
  // TRD – харьцангуй нягт (ерөнхий хувилбар)
  // --------------------------------------------------
  function renderTrd(data) {
    const p = getP(data);
    let html =
      '<table class="table table-sm table-bordered mb-0" ' +
      'style="font-size:0.8em;width:100%;margin:0;">' +
      '<thead class="table-light">' +
      '<tr>' +
      '<th>Бортого №</th>' +
      '<th>Нүүрсний масс (m)</th>' +
      '<th>Бортого + дээж + ус (m1)</th>' +
      '<th>Үр дүн (TRD)</th>' +
      '</tr></thead><tbody>';

    html += '<tr>' +
      '<td>' + esc(p.p1.num || p.p1.bottle || '-') + '</td>' +
      '<td>' + fmt(p.p1.m2, 4) + '</td>' +
      '<td>' + fmt(p.p1.m1, 4) + '</td>' +
      '<td>' + fmt(p.p1.result, 3) + '</td>' +
      '</tr>';

    html += '<tr>' +
      '<td>' + esc(p.p2.num || p.p2.bottle || '-') + '</td>' +
      '<td>' + fmt(p.p2.m2, 4) + '</td>' +
      '<td>' + fmt(p.p2.m1, 4) + '</td>' +
      '<td>' + fmt(p.p2.result, 3) + '</td>' +
      '</tr>';

    if (data && (data.diff != null || data.avg != null)) {
      html += '<tr>' +
        '<td colspan="4">' +
        (data.avg != null ? '<strong>avg:</strong> ' + fmt(data.avg, 3) : '') +
        (data.diff != null ? ' | <strong>Δ:</strong> ' + fmt(data.diff, 3) : '') +
        '</td>' +
        '</tr>';
    }

    html += '</tbody></table>';
    return html;
  }

  // --------------------------------------------------
  // Нийт хүхэр / P / Cl / F / CV – generic 2 параллель
  // --------------------------------------------------
  function renderGenericP1P2Percent(data, labelPercent) {
    const p = getP(data);
    labelPercent = labelPercent || '%';
    let html =
      '<table class="table table-sm table-bordered mb-0" ' +
      'style="font-size:0.8em;width:100%;margin:0;">' +
      '<thead class="table-light">' +
      '<tr>' +
      '<th></th>' +
      '<th>Масс (g)</th>' +
      '<th>' + esc(labelPercent) + '</th>' +
      '</tr></thead><tbody>';

    html += '<tr>' +
      '<td>p1</td>' +
      '<td>' + fmt(p.p1.m2, 4) + '</td>' +
      '<td>' + fmt(p.p1.result, 3) + '</td>' +
      '</tr>';

    html += '<tr>' +
      '<td>p2</td>' +
      '<td>' + fmt(p.p2.m2, 4) + '</td>' +
      '<td>' + fmt(p.p2.result, 3) + '</td>' +
      '</tr>';

    if (data && (data.diff != null || data.avg != null)) {
      html += '<tr>' +
        '<td colspan="3">' +
        (data.avg != null ? '<strong>avg:</strong> ' + fmt(data.avg, 3) + ' ' + esc(labelPercent) : '') +
        (data.diff != null ? ' | <strong>Δ:</strong> ' + fmt(data.diff, 3) : '') +
        '</td>' +
        '</tr>';
    }

    html += '</tbody></table>';
    return html;
  }

  function renderSulfur(data)     { return renderGenericP1P2Percent(data, 'S (ad), %'); }
  function renderPhosphorus(data) { return renderGenericP1P2Percent(data, 'P (ad), %'); }
  function renderChlorine(data)   { return renderGenericP1P2Percent(data, 'Cl (ad), %'); }
  function renderFluorine(data)   { return renderGenericP1P2Percent(data, 'F (ad), %'); }
  function renderCv(data)         { return renderGenericP1P2Percent(data, 'Q (cal/g)'); }

  // --------------------------------------------------
  // MAIN MAP – base код → renderer
  // --------------------------------------------------
  const MINI_TABLE_RENDERERS = {
    'Aad':   renderAad,
    'Mad':   renderMad,
    'Vad':   renderVad,
    'MT':    renderMt,
    'CSN':   renderCsn,
    'Gi':    renderGi,
    'TRD':   renderTrd,
    'TS':    renderSulfur,
    'P':     renderPhosphorus,
    'Cl':    renderChlorine,
    'F':     renderFluorine,
    'CV':    renderCv,
    'Qgr':   renderCv,
    'SOLID': renderDefaultRaw // одоохондоо raw-оор
  };

  // --------------------------------------------------
  // ALIAS_MAP – canonical/alias → base code
  // (constants.py-ийн CANONICAL_TO_BASE_ANALYSIS + aliases)
  // --------------------------------------------------
  const ALIAS_MAP = {
    // canonical нэршлүүд
    'total_moisture': 'MT',
    'inherent_moisture': 'Mad',
    'ash': 'Aad',
    'volatile_matter': 'Vad',
    'total_sulfur': 'TS',
    'phosphorus': 'P',
    'total_chlorine': 'Cl',
    'total_fluorine': 'F',
    'calorific_value': 'CV',
    'free_swelling_index': 'CSN',
    'caking_power': 'Gi',
    'relative_density': 'TRD',
    'plastometer_x': 'X',
    'plastometer_y': 'Y',
    'coke_reactivity_index': 'CRI',
    'coke_strength_after_reaction': 'CSR',
    'mass': 'm',
    'free_moisture': 'FM',
    'solid': 'SOLID',

    // түгээмэл алиасууд
    'mt': 'MT',
    'mt,ar': 'MT',
    'mad': 'Mad',
    'm,ad': 'Mad',
    'aad': 'Aad',
    'a,ad': 'Aad',
    'ash (ad)': 'Aad',
    'vad': 'Vad',
    'v,ad': 'Vad',
    'volatile matter': 'Vad',
    'st,ad': 'TS',
    'ts': 'TS',
    'p,ad': 'P',
    'p': 'P',
    'cl,ad': 'Cl',
    'cl': 'Cl',
    'f,ad': 'F',
    'f': 'F',
    'qgr,ad': 'CV',
    'qgr': 'Qgr',
    'cv': 'CV',
    'csn': 'CSN',
    'gi': 'Gi',
    'trd': 'TRD',
    'fm': 'FM',
    'solid': 'SOLID'
  };

  function normalizeCode(code) {
    if (!code) return '';
    const raw = String(code).trim();
    const lc  = raw.toLowerCase();

    if (ALIAS_MAP[lc]) {
      return ALIAS_MAP[lc];
    }

    // эхний үсэгнүүдийг аваад (Vad.d → Vad) шалгана
    const m = raw.match(/^[a-zA-Z]+/);
    if (m && MINI_TABLE_RENDERERS[m[0]]) {
      return m[0];
    }

    return raw;
  }

  // --------------------------------------------------
  // Нэгтгэсэн API
  // --------------------------------------------------
  function renderMiniTable(analysisCode, rawData) {
    const base = normalizeCode(analysisCode);
    const fn   = MINI_TABLE_RENDERERS[base];

    // debug-д
    // console.log'[mini] code=', analysisCode, '→ base=', base, 'hasRenderer=', !!fn (removed for production)

    if (!fn) {
      return renderDefaultRaw(rawData);
    }

    try {
      return fn(rawData || {});
    } catch (e) {
      console.error('mini table render error', e, analysisCode, rawData);
      return renderDefaultRaw(rawData);
    }
  }

  window.MINI_TABLE_RENDERERS = MINI_TABLE_RENDERERS;
  window.renderMiniTable = renderMiniTable;
})();
