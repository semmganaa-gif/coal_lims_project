/* static/js/calculators/TRD_calculator.js (ШИНЭЧИЛСЭН - Үр дүнг хадгалах үед харуулдаг болсон) */
(function () {
  const TABLE_ID = '#trd-analysis-table';
  const $tbl = document.querySelector(TABLE_ID);
  if (!$tbl) return;

  // --- Тохиргоо ---
  const BOTTLE_CACHE = {}; // Бортогоны жингийн кэш (serial -> {avg_value, ...})
  const MAD_BY_SAMPLE = window.MAD_BY_SAMPLE || {};
  const TOL_INPUT = () => document.getElementById('trd-tol');
  const TEMP_INPUT = () => document.getElementById('trd-temp-c');
  const ANALYSIS_CODE = 'TRD'; // Хадгалах үед ашиглана
  
  // (!!! ШИНЭ) Тооцоолсон үр дүнг хадгалах нууц сан
  window.TRD_RESULTS_CACHE = {};

  // --- Туслах функцууд ---

  // Kt хүснэгт (6..35 °C) – стандартын утгууд
  const KT_TABLE = {
     6:1.00174,  7:1.00170,  8:1.00165,  9:1.00158, 10:1.00150, 11:1.00140, 12:1.00129,
    13:1.00117, 14:1.00100, 15:1.00090, 16:1.00074, 17:1.00057, 18:1.00039, 19:1.00020,
    20:1.00000, 21:0.99979, 22:0.99956, 23:0.99953, 24:0.99909, 25:0.99883, 26:0.99857,
    27:0.99831, 28:0.99804, 29:0.99773, 30:0.99743, 31:0.99712, 32:0.99682, 33:0.99649,
    34:0.99616, 35:0.99582
  };

  /**
   * Input-ээс ТООн утга унших (null-safe)
   */
  function num(el) {
    if (!el) return null;
    const s = String(el.value ?? '').trim().replace(',', '.');
    if (!s) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  }
  
  /**
   * Input-ээс ТЕКСТ утга унших (null-safe)
   */
  function str(el) {
    if (!el) return null;
    return String(el.value ?? '').trim();
  }
  
  function numById(id) {
    return num(document.getElementById(id));
  }

  function strById(id) {
    return str(document.getElementById(id));
  }

  /**
   * Температураас Kt коэффициент тооцох (шугаман интерполяц)
   */
  function ktFromTemp(t) {
    t = Number(t);
    if (isNaN(t)) return 1.0; // default 20°C
    if (t <= 6) return KT_TABLE[6];
    if (t >= 35) return KT_TABLE[35];
    
    const t0 = Math.floor(t), t1 = Math.ceil(t);
    if (t0 === t1) return KT_TABLE[t0] ?? 1.0; 
    
    const k0 = KT_TABLE[t0], k1 = KT_TABLE[t1];
    if (k0 == null || k1 == null) return 1.0; 

    const w = (t - t0); 
    return k0 + (k1 - k0) * w;
  }

  /**
   * API-аас бортогоны жинг (m2) кэшлэн авчрах
   */
  async function fetchBottle(serial) {
    const key = (serial || '').trim();
    if (!key) return null;
    if (BOTTLE_CACHE[key]) return BOTTLE_CACHE[key];
    try {
      const resp = await fetch(`/settings/api/bottle/${encodeURIComponent(key)}/active`);
      if (!resp.ok) {
         console.error(`Bottle API ${resp.status}: ${serial}`);
         return null;
      }
      const js = await resp.json();
      const d = js.data || js;
      if (js && js.success && typeof d.avg_value === 'number') {
        BOTTLE_CACHE[key] = { avg_value: d.avg_value, temperature_c: d.temperature_c };
        return BOTTLE_CACHE[key];
      }
    } catch (e) {
      console.error(`Bottle API fetch error: ${e.message}`);
    }
    return null;
  }

  /**
   * Харьцангуй нягтын томьёо (TRD)
   */
  function calcTRD(m, m1, m2, mad, kt) {
    m = Number(m); m1 = Number(m1); m2 = Number(m2); mad = Number(mad);
    if ([m, m1, m2, mad, kt].some(x => x == null || isNaN(x))) return null;

    const md = m * (100.0 - mad) / 100.0;
    const denom = md + m2 - m1;
    if (denom <= 0) return null; 

    return (md / denom) * kt;
  }

  /**
   * (Global функц)
   * (!!! ШИНЭЧЛЭЛ) Энэ функц одоо тооцоолоод, дэлгэцэнд харуулахгүйгээр
   * зөвхөн `window.TRD_RESULTS_CACHE`-д хадгална.
   */
  window.calculateAndDisplayForRow = async function (sampleId, lockInputs = false) {
    // lockInputs-г үл тоомсорлоно, зөвхөн 'collect' функц л түгжинэ.
    
    const tr1 = $tbl.querySelector(`tr[data-sample-id="${sampleId}"][data-parallel="1"]`);
    const tr2 = $tbl.querySelector(`tr[data-sample-id="${sampleId}"][data-parallel="2"]`);
    if (!tr1 || !tr2) return null; 

    const cell1 = tr1.querySelector(`.trd-cell[data-parallel="1"]`);
    const cell2 = tr2.querySelector(`.trd-cell[data-parallel="2"]`);

    // --- Глобал утгуудыг авах ---
    const kt = ktFromTemp(TEMP_INPUT()?.value ?? 20.0);
    const mad = Number(MAD_BY_SAMPLE[sampleId]);

    if (isNaN(mad)) {
      cell1.textContent = 'Mad missing!'; cell1.classList.add('text-danger');
      cell2.textContent = 'Mad missing!'; cell2.classList.add('text-danger');
      window.TRD_RESULTS_CACHE[sampleId] = null; // Тооцоолох боломжгүй
      return null;
    } else {
      cell1.classList.remove('text-danger');
      cell2.classList.remove('text-danger');
    }

    // --- P1-ийн утгуудыг унших ба m2-г татах ---
    const p1_bottle_s = strById(`sample_${sampleId}_p1_bottle`);
    const p1_m  = numById(`sample_${sampleId}_p1_m`);
    const p1_m1 = numById(`sample_${sampleId}_p1_m1`);
    const bottle1_data = await fetchBottle(p1_bottle_s);
    const p1_m2 = bottle1_data ? bottle1_data.avg_value : null;

    // --- P2-ын утгуудыг унших ба m2-г татах ---
    const p2_bottle_s = strById(`sample_${sampleId}_p2_bottle`);
    const p2_m  = numById(`sample_${sampleId}_p2_m`);
    const p2_m1 = numById(`sample_${sampleId}_p2_m1`);
    const bottle2_data = await fetchBottle(p2_bottle_s);
    const p2_m2 = bottle2_data ? bottle2_data.avg_value : null;

    // --- Тооцоолол ---
    const r1 = calcTRD(p1_m, p1_m1, p1_m2, mad, kt);
    const r2 = calcTRD(p2_m, p2_m1, p2_m2, mad, kt);

    let avg = null, diff = null;

    // Урьдчилсан дундаж → тохирцын зөрүүг сонгох (TRD >= 4.0 бол 0.04)
    let prelimAvg = null;
    if (r1 != null && r2 != null) prelimAvg = (r1 + r2) / 2.0;
    else if (r1 != null) prelimAvg = r1;

    const tol = (typeof getRepeatabilityLimit === 'function' && prelimAvg != null)
      ? (getRepeatabilityLimit('TRD', prelimAvg) ?? 0.02)
      : 0.02;

    // Tolerance input-г шинэчлэх (мэдээллийн зориулалтаар)
    const tolInput = TOL_INPUT();
    if (tolInput) tolInput.value = tol;

    if (r1 != null && r2 != null) {
      diff = Math.abs(r1 - r2);
      if (diff <= tol) {
        avg = (r1 + r2) / 2.0;
      }
    } else if (r1 != null && (p2_m == null && p2_m1 == null)) { // P2 хоосон, зөвхөн P1-тэй
      avg = r1;
      diff = 0; // Ганц утга тул зөрүү 0
    }

    // (!!! ШИНЭЧЛЭЛ) Дэлгэцэнд харуулахгүй, кэш рүү хадгална
    window.TRD_RESULTS_CACHE[sampleId] = {
        r1, r2, diff, avg, kt, tol, mad,
        p1_data: { bottle: p1_bottle_s, m: p1_m, m1: p1_m1, m2_fetched: p1_m2 },
        p2_data: { bottle: p2_bottle_s, m: p2_m, m1: p2_m1, m2_fetched: p2_m2 }
    };

    return null; // Payload буцаахгүй
  };

  /**
   * "Хадгалах" товч дарахад дуудагдах функц.
   * (!!! ШИНЭЧЛЭЛ) Энэ функц одоо тооцооллыг кэшээс авч, дэлгэцэнд харуулж,
   * input-г түгжиж, payload-г буцаана.
   */
  function collectTRDPayload() {
    // Removed console.log for production
    const payload = [];
    
    const p1Rows = $tbl.querySelectorAll('tbody tr[data-parallel="1"]');
      
    p1Rows.forEach(tr1 => {
      const sampleId = tr1.dataset.sampleId;
      const tr2 = $tbl.querySelector(`tr[data-sample-id="${sampleId}"][data-parallel="2"]`);
      if (!tr2) return; 

      // --- 1. Нууц кэшээс тооцооллыг унших ---
      const data = window.TRD_RESULTS_CACHE[sampleId];
      
      // Дундаж тооцоологдоогүй бол (Mad алга, утга дутуу г.м) хадгалахгүй
      if (!data || data.avg == null || isNaN(data.avg)) {
          // Mad-ын алдааг дахин харуулах
          if (isNaN(MAD_BY_SAMPLE[sampleId])) {
              const cell1 = tr1.querySelector(`.trd-cell[data-parallel="1"]`);
              const cell2 = tr2.querySelector(`.trd-cell[data-parallel="2"]`);
              cell1.textContent = 'Mad missing!'; cell1.classList.add('text-danger');
              cell2.textContent = 'Mad missing!'; cell2.classList.add('text-danger');
          }
          return;
      }

      // --- 2. Үр дүнг ДЭЛГЭЦЭНД ХАРУУЛАХ ---
      const cell1 = tr1.querySelector(`.trd-cell[data-parallel="1"]`);
      const cell2 = tr2.querySelector(`.trd-cell[data-parallel="2"]`);
      const diffCell = tr1.querySelector(`.trd-diff`);
      const avgCell = tr1.querySelector(`.trd-avg`);

      cell1.textContent = (data.r1 != null) ? data.r1.toFixed(3) : '-';
      cell2.textContent = (data.r2 != null) ? data.r2.toFixed(3) : '-';
      avgCell.textContent = data.avg.toFixed(3);
      
      if (data.diff != null) {
          diffCell.textContent = data.diff.toFixed(3);
          if (data.diff <= data.tol) {
              diffCell.classList.add('text-success');
              diffCell.classList.remove('text-danger', 'fw-bold');
          } else {
              diffCell.classList.remove('text-success');
              diffCell.classList.add('text-danger', 'fw-bold');
          }
      } else {
          diffCell.textContent = '-';
          diffCell.classList.remove('text-success', 'text-danger', 'fw-bold');
      }

      // --- 3. Payload бэлтгэх ---
      payload.push({
        sample_id: Number(sampleId),
        analysis_code: ANALYSIS_CODE,
        final_result: Number(data.avg.toFixed(4)),
        raw_data: {
          p1: {
            bottle: data.p1_data.bottle, 
            m: data.p1_data.m, 
            m1: data.p1_data.m1,
            m2_fetched: data.p1_data.m2_fetched,
            result: (data.r1 != null) ? Number(data.r1.toFixed(4)) : null
          },
          p2: {
            bottle: data.p2_data.bottle, 
            m: data.p2_data.m, 
            m1: data.p2_data.m1,
            m2_fetched: data.p2_data.m2_fetched,
            result: (data.r2 != null) ? Number(data.r2.toFixed(4)) : null
          },
          avg: Number(data.avg.toFixed(4)),
          diff: (data.diff != null) ? Number(data.diff.toFixed(4)) : null,
          mad_used: Number(data.mad.toFixed(4)),
          kt_used: Number(data.kt.toFixed(6)),
          temp_c_used: Number(TEMP_INPUT()?.value ?? 20.0),
          limit_used: data.tol
        }
      });

      // --- 4. Input-уудыг түгжих ---
      tr1.querySelectorAll('.form-input').forEach(inp => {
        inp.readOnly = true; inp.classList.add('bg-light');
      });
      tr2.querySelectorAll('.form-input').forEach(inp => {
        inp.readOnly = true; inp.classList.add('bg-light');
      });
    }); // end forEach
    
    return payload;
  } // end collectTRDPayload

  /**
   * `collectTRDPayload` функцийг LIMS-ийн үндсэн хадгалах системд бүртгэх
   */
  function installCollector() {
    if (!window.LIMS_CALC) window.LIMS_CALC = {};
    window.LIMS_CALC[ANALYSIS_CODE] = {
      collect: collectTRDPayload
    };
    // Removed console.log for production
  }

  // --- Event Listeners ---

  /**
   * Input-д өөрчлөлт орох бүрт тооцоог цэвэрлэж, дахин бодно.
   */
  $tbl.addEventListener('input', async (e) => {
    if (!e.target.classList.contains('form-input')) return;
    const tr = e.target.closest('tr[data-sample-id]');
    if (!tr) return;

    const sampleId = tr.dataset.sampleId;
    
    // (!!! ШИНЭЧЛЭЛ) Зөвхөн цэвэрлэх (Дахин бодохыг харуулахгүй)
    const cell1 = $tbl.querySelector(`.trd-cell[data-sample-id="${sampleId}"][data-parallel="1"]`);
    const cell2 = $tbl.querySelector(`.trd-cell[data-sample-id="${sampleId}"][data-parallel="2"]`);
    const diffCell = $tbl.querySelector(`.trd-diff[data-sample-id="${sampleId}"]`);
    const avgCell = $tbl.querySelector(`.trd-avg[data-sample-id="${sampleId}"]`);

    if (cell1) cell1.textContent = '-';
    if (cell2) cell2.textContent = '-';
    if (diffCell) {
      diffCell.textContent = '-';
      diffCell.classList.remove('text-success', 'text-danger', 'fw-bold');
    }
    if (avgCell) avgCell.textContent = '-';

    // (!!! ШИНЭЧЛЭЛ) Тооцооллыг цаана нь нууцаар хийж, кэшлэх
    await window.calculateAndDisplayForRow(sampleId, false);
  });
  
  /**
   * Глобал тохиргоо (Temp, Tol) өөрчлөгдвөл бүх мөрийг дахин тооцоолно.
   */
  [TEMP_INPUT(), TOL_INPUT()].forEach(inp => {
    if (!inp) return;
    inp.addEventListener('input', async () => {
      const rows = $tbl.querySelectorAll('tbody tr[data-parallel="1"]');
      // Бүх мөрийг зэрэг дахин тооцоолно (цаана нь)
      const promises = Array.from(rows).map(tr => 
        window.calculateAndDisplayForRow(tr.dataset.sampleId, false)
      );
      await Promise.all(promises);
    });
  });

  // DOM ачаалахад хадгалах функцийг бүртгэх
  document.addEventListener('DOMContentLoaded', () => {
    installCollector();
    
    // (!!! ШИНЭ) Ачаалахад буцааж дүүргэсэн утгуудыг мөн цаана нь тооцоолох
    // (HTML доторх 'DOMContentLoaded' скрипт нь зөвхөн утгуудыг буцааж дүүргэдэг)
    setTimeout(async () => {
      const rows = $tbl.querySelectorAll('tbody tr[data-parallel="1"]');
      const promises = Array.from(rows).map(tr => {
        // Хэрэв утгатай бол л дахин тооцоолно
        const p1_m = numById(`sample_${tr.dataset.sampleId}_p1_m`);
        if (p1_m != null) {
          return window.calculateAndDisplayForRow(tr.dataset.sampleId, false);
        }
        return Promise.resolve();
      });
      await Promise.all(promises);
    }, 200); // 200ms хүлээж HTML-ийн скриптийг ажиллуулж дуусгана
    
  });

})();