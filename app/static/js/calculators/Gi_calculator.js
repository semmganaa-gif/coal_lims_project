/* static/js/calculators/Gi_calculator.js (УХААЛАГ ХУВИЛБАР)
 * НЭГ файл, ХОЁР томъёо.
 *
 * ДҮРЭМ:
 * 1) Хуудас ачаалахад Python-оос ирдэг window.GI_RETEST_MODES map-ийг шалгана.
 * 2) Хэрэв тухайн мөр "retest" (давтан) горимд бол 3:3 томъёог ашиглана.
 * 3) Эсрэг тохиолдолд 5:1 томъёог ашиглана.
 * 4) 5:1 горимд avg < 18 бол 'is_low_avg: true' туг илгээнэ (3:3-аар дахин хийх зөвлөмж).
 */

(function () {
  // ---------- ТОХИРГОО ----------
  const ANALYSIS_CODE = 'Gi';                  // Зөвхөн 'Gi'
  const TABLE_SEL = '#Gi-analysis-table';
  const MIN_AVG_THRESHOLD = 18;                // 18-аас бага бол 5:1 горимд хүчингүй гэж үзнэ
  const REPEATABILITY_LIMIT = getRepeatabilityLimit('Gi') ?? 2;               // T (жишээ давтагдах чадварын хязгаар)

  // Python-оос ирэх: жишээ нь { "120": true, "121": false }
  // true  -> 3:3 горим; false/undef -> 5:1 горим
  const RETEST_MODES = window.GI_RETEST_MODES || {};

  // ---------- DOM Utility ----------
  const $table = document.querySelector(TABLE_SEL);
  if (!$table) return;

  const getRefs = (sampleId) => {
    const p1_row = $table.querySelector(`tr[data-sample-id="${sampleId}"][data-parallel="1"]`);
    const p2_row = $table.querySelector(`tr[data-sample-id="${sampleId}"][data-parallel="2"]`);
    if (!p1_row || !p2_row) return null;

    return {
      p1: {
        num: p1_row.querySelector(`#sample_${sampleId}_p1_num`),
        m1:  p1_row.querySelector(`#sample_${sampleId}_p1_m1`), // LIMS: Масс-1 (Стандарт: m)
        m2:  p1_row.querySelector(`#sample_${sampleId}_p1_m2`), // LIMS: Масс-2 (Стандарт: m1)
        m3:  p1_row.querySelector(`#sample_${sampleId}_p1_m3`), // LIMS: Масс-3 (Стандарт: m2)
        res: p1_row.querySelector(`.result-cell[data-parallel="1"]`)
      },
      p2: {
        num: p2_row.querySelector(`#sample_${sampleId}_p2_num`),
        m1:  p2_row.querySelector(`#sample_${sampleId}_p2_m1`),
        m2:  p2_row.querySelector(`#sample_${sampleId}_p2_m2`),
        m3:  p2_row.querySelector(`#sample_${sampleId}_p2_m3`),
        res: p2_row.querySelector(`.result-cell[data-parallel="2"]`)
      },
      diff: p1_row.querySelector(`.diff-cell`),
      avg:  p1_row.querySelector(`.avg-cell`),
      calc: p1_row.querySelector(`.calc-cell`)
    };
  };

  const val = (el) => {
    if (!el) return null;
    const s = (el.value ?? '').toString().trim();
    if (s === '') return null;
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : null;
  };

  // (m1, m2, m3-аас үр дүн тооцох)
  // mode: '3_3' эсвэл '5_1'
  const calculateResult = (m1_val, m2_val, m3_val, mode) => {
    if (m1_val === null || m2_val === null || m3_val === null || m1_val === 0) {
      return null;
    }

    let result;
    if (mode === '3_3') {
      // Gi (3:3): Gi = (30*m2 + 70*m3) / (5*m1)
      result = ((30 * m2_val) + (70 * m3_val)) / (5 * m1_val);
    } else {
      // Gi (5:1): Gi = 10 + (30*m2 + 70*m3) / m1
      result = 10 + ((30 * m2_val) + (70 * m3_val)) / m1_val;
    }

    const rounded = Math.round(result);
    return Number.isFinite(rounded) ? rounded : null;
  };

  // ----- Үндсэн тооцоолох функц -----
  window.calculateAndDisplayForRow = function(sampleId, isSaving = false) {
    const refs = getRefs(sampleId);
    if (!refs) return null;

    // Горим тодорхойлох: true -> 3:3, else -> 5:1
    const mode = RETEST_MODES[String(sampleId)] ? '3_3' : '5_1';

    const p1_m1 = val(refs.p1.m1), p1_m2 = val(refs.p1.m2), p1_m3 = val(refs.p1.m3);
    const p2_m1 = val(refs.p2.m1), p2_m2 = val(refs.p2.m2), p2_m3 = val(refs.p2.m3);

    const p1_res = calculateResult(p1_m1, p1_m2, p1_m3, mode);
    const p2_res = calculateResult(p2_m1, p2_m2, p2_m3, mode);

    refs.p1.res.textContent = (p1_res !== null) ? p1_res : '-';
    refs.p2.res.textContent = (p2_res !== null) ? p2_res : '-';

    let avg = null, diff = null, t_exceeded = false, is_low_avg = false;

    if (p1_res !== null && p2_res !== null) {
      avg  = (p1_res + p2_res) / 2;
      diff = Math.abs(p1_res - p2_res);
      t_exceeded = (diff > REPEATABILITY_LIMIT);

      refs.diff.textContent = diff.toFixed(0);
      refs.avg.textContent  = Math.round(avg).toString();
    } else {
      refs.diff.textContent = '-';
      refs.avg.textContent  = '-';
    }

    // Горимоос хамаарах дүрэм
    let saveable = false;
    if (avg === null) {
      refs.calc.innerHTML = '-';
      saveable = false;
    } else if (mode === '5_1' && avg < MIN_AVG_THRESHOLD) {
      // 5:1 горимд 18-аас бага бол 3:3-аар дахин шинжилнэ
      refs.calc.innerHTML = `<span class="text-danger fw-bold">Дундаж &lt; ${MIN_AVG_THRESHOLD}.<br>3:3 харьцаагаар дахин шинжил.</span>`;
      is_low_avg = true;
      saveable = true; // сервер рүү тугаа илгээхийн тулд хадгалж болно
    } else {
      is_low_avg = false;
      if (t_exceeded) {
        refs.calc.innerHTML = `<span class="text-warning">T &gt; ${REPEATABILITY_LIMIT} (Хэтэрсэн)</span>`;
      } else {
        refs.calc.innerHTML = `<span class="text-success">T ≤ ${REPEATABILITY_LIMIT} (Тохирсон)</span>`;
      }
      saveable = true;
    }

    if (isSaving && saveable) {
      return {
        sample_id: Number(sampleId),
        analysis_code: ANALYSIS_CODE,
        final_result: Math.round(avg),   // серверт бүхэллэсэн дүн явуулна
        raw_data: {
          p1: { num: refs.p1.num?.value ?? '', m1: p1_m1, m2: p1_m2, m3: p1_m3, result: p1_res },
          p2: { num: refs.p2.num?.value ?? '', m1: p2_m1, m2: p2_m2, m3: p2_m3, result: p2_res },
          avg: avg,
          diff: diff,
          t_exceeded: t_exceeded,
          is_low_avg: is_low_avg,     // 5:1 горимд 18-аас доош болсон тэмдэг
          retest_mode: mode,          // аль томъёо хэрэглэснээ серверт мэдээлнэ
          limit_used: REPEATABILITY_LIMIT,
          limit_mode: "abs"
        }
      };
    }

    return null;
  };

  // ----- Event listeners (DOM restore, input хадгалалт) -----
  (function setupSharedListeners() {
    const k  = (id) => `analysis_${ANALYSIS_CODE}_${id}`;
    const sv = (id, v) => { try { sessionStorage.setItem(k(id), String(v ?? '')); } catch(e){} };
    const gv = (id) => { try { const v = sessionStorage.getItem(k(id)); return (v==null?'':v); } catch(e){ return '' } };

    // Хуудас ачаалахад — input-уудыг сэргээж, хэрэв утгатай бол тооцоог харуулна
    document.addEventListener('DOMContentLoaded', () => {
      $table.querySelectorAll('tbody tr[data-sample-id]').forEach(tr => {
        const sid = tr.dataset.sampleId;
        if (!sid) return;

        let hasSaved = false;
        tr.querySelectorAll('input.form-input').forEach(inp => {
          const saved = gv(inp.id);
          if (saved !== '') {
            inp.value = saved;
            hasSaved = true;
          }
        });

        if (hasSaved) {
          window.calculateAndDisplayForRow(sid, false);
        }
      });
    });

    // Оролтын өөрчлөлт дээр — зөвхөн sessionStorage-д хадгална (шууд тооцохгүй)
    $table.addEventListener('input', (e) => {
      const inp = e.target;
      if (!inp.classList || !inp.classList.contains('form-input')) return;
      sv(inp.id, inp.value ?? '');
      // Шууд тооцоолох хэсгийг хэрэглэгчийн хүсэлтээр арилгасан.
      // Тооцоо зөвхөн "Хадгалах" дарж байж хийгдэнэ.
    });
  })();

})();
