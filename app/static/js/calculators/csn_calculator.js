/* static/js/calculators/csn_calculator.js (ЗАСВАРЛАСАН)
 * ШИНЭ ДҮРЭМ:
 * - "Хадгалах" товч дарагдахад `window.csnCalc.collectPayload` дуудагдана.
 * - Энэ нь ЗӨВХӨН ЗАСАГДСАН (түгжигдээгүй) мөрүүдийг цуглуулна.
 * - Input дээр бичих үед тооцоог харуулахгүй, зөвхөн "-" болгоно.
 * - Тооцоо (T, Дундаж) зөвхөн хадгалсны ДАРАА харагдана.
 */

(function () {
  // ---------- ТОХИРГОО ----------
  const ANALYSIS_CODE = window.LIMS_ANALYSIS_CODE || 'CSN';
  const TABLE_SEL = '#csn-analysis-table';
  const LIMIT_T = getRepeatabilityLimit('CSN') ?? 0.5; // CSN-ийн тохирцын дээд хязгаар

  const $table = document.querySelector(TABLE_SEL);
  if (!$table) {
    console.warn('CSN: хүснэгт олдсонгүй:', TABLE_SEL);
    return;
  }

  // ---------- sessionStorage helper ----------
  const k = (id) => `analysis_${ANALYSIS_CODE}_${id}`;
  function sv(id, val) { try { sessionStorage.setItem(k(id), String(val ?? '')); } catch(e){} }
  function gv(id) { try { const v = sessionStorage.getItem(k(id)); return (v==null?'':v); } catch(e){ return '' } }
  function rm(id) { try { sessionStorage.removeItem(k(id)); } catch(e){} }

  // ---------- Мөрийн лавлагаа ----------
  function refs(sampleId) {
    const tr = $table.querySelector(`tbody tr[data-sample-id="${sampleId}"]`);
    if (!tr) return null;

    const nums = tr.querySelectorAll('td input[type="number"]');
    const v1 = nums[0] || null, v2 = nums[1] || null, v3 = nums[2] || null, v4 = nums[3] || null, v5 = nums[4] || null;

    // csn_form.html-д нийт 10 багана (✓ байхгүй)
    // ... v3 | v4 | v5 | T (8) | avg (9) | calc (10)
    const cells = tr.querySelectorAll('td');
    const tCell = cells[7] || null;    // 8 дахь нүд
    const avgCell = cells[8] || null;  // 9 дэх нүд
    const calcCell = cells[9] || null; // 10 дахь нүд

    return { tr, v1, v2, v3, v4, v5, tCell, avgCell, calcCell };
  }

  // ---------- Тоон туслахууд ----------
  const val = x => {
    const s = (x?.value ?? '').toString().trim().replace(',', '.');
    if (!s) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  };
  const isHalf = x => x !== null && Math.abs(x * 2 - Math.round(x * 2)) < 1e-9;
  const valid  = x => x !== null && x >= 0 && x <= 9 && isHalf(x);
  const half   = x => Math.round(x * 2) / 2;

  // ===== CSN тооцоо: (доод тал нь 2 утга шаардлагатай) =====
  function computeRow(sid) {
    const r = refs(sid); if(!r) return null;

    const v1 = val(r.v1), v2 = val(r.v2), v3 = val(r.v3), v4 = val(r.v4), v5 = val(r.v5);
    const values = [v1, v2, v3, v4, v5].filter(valid);
    
    // Доод тал нь 2 зөв утга байхгүй бол тооцоо хийхгүй
    if(values.length < 2) return null;

    const avg_raw = values.reduce((a,b)=>a+b,0) / values.length;
    const avg = half(avg_raw);
    const mx = Math.max(...values), mn = Math.min(...values);
    const t  = Math.abs(mx - mn);
    const t_exceeded = (t > LIMIT_T);

    return { v1, v2, v3, v4, v5, avg, t, n_used: values.length, t_exceeded };
  }
  
  // ===== Хадгалсны дараа DOM-ыг шинэчлэх (analysis_page.html-аас дуудагдана) =====
  window.renderSavedCSN = function(sid, data) {
    const r = refs(sid); if(!r) return;

    // input-үүдийг түгжинэ
    [r.v1,r.v2,r.v3,r.v4,r.v5].forEach(inp=>{
      if(!inp) return;
      inp.readOnly = true; inp.classList.add('bg-light');
      sv(inp.id + '_locked', 'true'); // sessionStorage-д түгжсэн тэмдэглэгээ
    });

    // T, Дундаж, Тооцооллыг зөвхөн хадгалсны дараа харуулна
    if(r.tCell)   r.tCell.textContent = (data.t != null) ? Number(data.t).toFixed(2) : '-';
    if(r.avgCell) r.avgCell.textContent = (data.avg != null) ? Number(data.avg).toFixed(1) : '-';
    if(r.calcCell) {
      if (data.t_exceeded) {
        r.calcCell.innerHTML = `<span class="text-danger">T > ${LIMIT_T} (Хэтэрсэн)</span>`;
      } else {
        r.calcCell.innerHTML = `<span class="text-success">T ≤ ${LIMIT_T} (Тохирсон)</span>`;
      }
    }
  }

  // ===== "Хадгалах" товч дарахад analysis_page.html энэ функцийг дуудна =====
  function collectPayload() {
    const payload = [];
    $table.querySelectorAll('tbody tr[data-sample-id]').forEach(tr => {
      const sid = tr.dataset.sampleId;
      const r = refs(sid);
      if (!r || r.v1.readOnly) {
        return; // Мөр олдсонгүй эсвэл өмнө нь хадгалж түгжсэн бол алгасна
      }
      
      const comp = computeRow(sid);
      if (!comp) {
        return; // Тооцоо хийх боломжгүй (утга дутуу) мөрийг алгасна
      }
      
      // Хадгалах боломжтой мөрийг payload-д нэмнэ
      payload.push({
        sample_id: Number(sid),
        analysis_code: ANALYSIS_CODE,
        final_result: comp.avg,
        raw_data: {
          v1:comp.v1, v2:comp.v2, v3:comp.v3, v4:comp.v4, v5:comp.v5,
          avg:comp.avg, t:comp.t, n_used: comp.n_used,
          limit_used: LIMIT_T,
          limit_mode: "abs",
          t_exceeded: comp.t_exceeded
        }
      });
    });
    return payload;
  }
  
  // Гадагш ил гаргана (LIMS_CALC namespace ашиглана)
  if (!window.LIMS_CALC) window.LIMS_CALC = {};
  window.LIMS_CALC.CSN = {
    collect: collectPayload
  };

  // Хуучин нэрийг мөн үлдээе (backward compatibility)
  window.csnCalc = {
    collectPayload: collectPayload
  };

  // ---------- DOM restore (сэргээх) ----------
  document.addEventListener('DOMContentLoaded', () => {
    $table.querySelectorAll('tbody tr[data-sample-id]').forEach(tr => {
      const sid = tr.dataset.sampleId;
      let isLocked = false;
      
      tr.querySelectorAll('td input[type="number"]').forEach(inp => {
        if(!inp.id) return;
        const saved = gv(inp.id);
        if(saved) inp.value = saved;
        if (gv(inp.id + '_locked') === 'true') {
          inp.readOnly = true;
          inp.classList.add('bg-light');
          isLocked = true;
        }
      });
      
      // Хэрэв түгжигдсэн (өмнө нь хадгалсан) бол тооцоог харуулна
      if (isLocked) {
        const comp = computeRow(sid); // Зүгээр тооцоолно
        if (comp) {
          // Зөвхөн хадгалсны дараа харуулдаг шинэ функцийг дуудна
          window.renderSavedCSN(sid, comp);
        }
      }
    });

    // input өөрчлөгдөх бүрт
    $table.addEventListener('input', (e) => {
      const inp = e.target;
      if(!(inp instanceof HTMLInputElement) || inp.type !== 'number') return;
      if(inp.readOnly) return;

      // Утгыг sessionStorage-д хадгална
      sv(inp.id, inp.value ?? '');
      
      const tr = inp.closest('tr[data-sample-id]');
      if(!tr) return;
      
      // !!! ШИНЭ ЛОГИК: Тооцоог харагдуулахгүй, "-" болгоно !!!
      const r = refs(tr.dataset.sampleId);
      if(r?.tCell)   r.tCell.textContent = '-';
      if(r?.avgCell) r.avgCell.textContent = '-';
      if(r?.calcCell) r.calcCell.textContent = '-';
    });
  });

})();
