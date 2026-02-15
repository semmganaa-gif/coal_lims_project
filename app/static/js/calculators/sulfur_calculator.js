/* static/js/calculators/sulfur_calculator.js
   St,ad (Total Sulfur, ad) — нэг мөрт (p1/p2 багана) хувилбар.
   - localStorage (fallback: sessionStorage)
   - зөвхөн SAVE үед түгжих
   - ахлахаас буцаасан мөрийг онгойлгох
   - сумтай навигац (↑/↓←/→), Enter = дараагийн талбар
*/
(function () {
  // ---- CONFIG ----
  const ANALYSIS_CODE = 'St,ad';
  const TABLE_SEL = '#sulfur-analysis-table';
  const REPEATABILITY_LIMIT = getRepeatabilityLimit('TS') ?? 0.05;   // T хязгаар (abs)
  const REJECTED_MAP = window.REJECTED_SAMPLES || {};
  const $table = document.querySelector(TABLE_SEL);
  if (!$table) return;

  // ---- Storage helpers (localStorage first) ----
  const storage = {
    set(k, v){ try{ localStorage.setItem(k, String(v ?? '')); }catch(e){} try{ sessionStorage.setItem(k, String(v ?? '')); }catch(e){} },
    get(k){ try{ const v = localStorage.getItem(k); if(v!==null) return v; }catch(e){} try{ const v2 = sessionStorage.getItem(k); return v2??''; }catch(e){} return '' },
    del(k){ try{ localStorage.removeItem(k); }catch(e){} try{ sessionStorage.removeItem(k); }catch(e){} }
  };
  const K = (id)=> `analysis_${ANALYSIS_CODE}_${id}`;

  // comma-той оролтыг зөвшөөрөх numeric parse
  function num(el){
    if(!el) return null;
    const s = String(el.value ?? '').trim().replace(',', '.');
    if (!s) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  }

  // ---- DOM refs (нэг мөрийн загвар) ----
  function refs(sampleId){
    const row = $table.querySelector(`tr[data-sample-id="${sampleId}"]`);
    if (!row) return null;
    return {
      row,
      p1: {
        weight: row.querySelector(`#sample_${sampleId}_p1_weight`),
        result: row.querySelector(`#sample_${sampleId}_p1_result`)
      },
      p2: {
        weight: row.querySelector(`#sample_${sampleId}_p2_weight`),
        result: row.querySelector(`#sample_${sampleId}_p2_result`)
      },
      diff: row.querySelector(`.diff-cell[data-sample-id="${sampleId}"]`),
      avg : row.querySelector(`.avg-cell[data-sample-id="${sampleId}"]`),
      calc: row.querySelector(`.calc-cell[data-sample-id="${sampleId}"]`)
    };
  }

  // ---- Core: тооцоолол + дэлгэц ----
  window.calculateAndDisplayForRow = function(sampleId, lockInputs=false){
    const r = refs(sampleId);
    if (!r) return null;

    const p1w = num(r.p1.weight);
    const p2w = num(r.p2.weight);
    const p1r = num(r.p1.result);
    const p2r = num(r.p2.result);

    let avg=null, diff=null, t_exceeded=false;

    // reset helper
    const resetCalcUI = ()=>{
      if (r.diff){ r.diff.textContent='-'; r.diff.classList.remove('text-success','text-danger','fw-bold'); r.diff.title=''; }
      if (r.avg)  r.avg.textContent='-';
      if (r.calc) r.calc.textContent='-';
    };

    if (p1r!=null && p2r!=null){
      avg  = (p1r+p2r)/2;
      diff = Math.abs(p1r-p2r);
      t_exceeded = diff > REPEATABILITY_LIMIT;

      if (r.diff){
        r.diff.textContent = diff.toFixed(2);
        r.diff.classList.remove('text-success','text-danger','fw-bold');
        if (t_exceeded){
          r.diff.classList.add('text-danger','fw-bold');
          r.diff.title = `T > ${REPEATABILITY_LIMIT} (exceeded)`;
        } else {
          r.diff.classList.add('text-success');
          r.diff.title = `T ≤ ${REPEATABILITY_LIMIT} (OK)`;
        }
      }
      if (r.avg) r.avg.textContent = avg.toFixed(3);
      if (r.calc) r.calc.innerHTML = t_exceeded
        ? `<span class="text-warning">T exceeded</span>`
        : `<span class="text-success">OK</span>`;
    } else if (p1r!=null && p2r==null){
      avg = p1r;
      resetCalcUI();
      if (r.avg) r.avg.textContent = avg.toFixed(3);
    } else if (p2r!=null && p1r==null){
      avg = p2r;
      resetCalcUI();
      if (r.avg) r.avg.textContent = avg.toFixed(3);
    } else {
      resetCalcUI();
    }

    // --- SAVE үед түгжиж + payload буцаана ---
    if (lockInputs && avg!=null){
      const isRejected = !!REJECTED_MAP[String(sampleId)];
      if (!isRejected){
        [r.p1.weight, r.p1.result, r.p2.weight, r.p2.result].forEach(inp=>{
          if(!inp) return;
          inp.readOnly = true;
          inp.classList.add('bg-light');
          storage.set(K(inp.id+'_locked'), 'true');
        });
      }
      return {
        sample_id: Number(sampleId),
        analysis_code: ANALYSIS_CODE,
        final_result: Number(avg.toFixed(4)),
        raw_data: {
          p1: { weight: Number.isFinite(p1w)? +p1w : null, result: Number.isFinite(p1r)? +Number(p1r.toFixed(4)) : null },
          p2: { weight: Number.isFinite(p2w)? +p2w : null, result: Number.isFinite(p2r)? +Number(p2r.toFixed(4)) : null },
          diff: Number.isFinite(diff)? +Number(diff.toFixed(4)) : null,
          avg:  +Number(avg.toFixed(4)),
          t_exceeded: !!t_exceeded,
          limit_used: REPEATABILITY_LIMIT,
          limit_mode: "abs"
        }
      };
    }
    return null;
  };

  // ---- Session/Local restore + rejected_UNLOCK ----
  document.addEventListener('DOMContentLoaded', ()=>{
    // restore inputs
    $table.querySelectorAll('tbody input.form-input').forEach(inp=>{
      const saved = storage.get(K(inp.id));
      if (saved !== '') inp.value = saved;

      const sid = inp.closest('tr[data-sample-id]')?.dataset.sampleId;
      const isRejected = sid && REJECTED_MAP[String(sid)];
      const wasLocked  = storage.get(K(inp.id+'_locked'))==='true';

      if (isRejected){
        inp.readOnly = false; inp.classList.remove('bg-light');
        storage.del(K(inp.id+'_locked'));
      } else if (wasLocked){
        inp.readOnly = true; inp.classList.add('bg-light');
      }
    });

    // түгжээтэй мөрүүдийн нэгтгэсэн үзүүлэлтийг зурна
    $table.querySelectorAll('tbody tr[data-sample-id]').forEach(tr=>{
      const sid = tr.dataset.sampleId;
      const anyInp = tr.querySelector('.form-input');
      const isRejected = !!REJECTED_MAP[String(sid)];
      if (anyInp && storage.get(K(anyInp.id+'_locked'))==='true' && !isRejected){
        window.calculateAndDisplayForRow(sid,false);
      }
    });
  });

  // ---- Persist on input, clear calc preview ----
  $table.addEventListener('input', (e)=>{
    const inp = e.target;
    if (!inp.classList.contains('form-input')) return;
    if (inp.readOnly) return;

    storage.set(K(inp.id), inp.value ?? '');

    const sid = inp.closest('tr[data-sample-id]')?.dataset.sampleId;
    if (!sid) return;
    const r = refs(sid);
    if (r){
      if (r.diff){ r.diff.textContent='-'; r.diff.classList.remove('text-success','text-danger','fw-bold'); r.diff.title=''; }
      if (r.avg)  r.avg.textContent='-';
      if (r.calc) r.calc.textContent='-';
    }
  });

  // ---- Keyboard navigation (↑/↓←/→, Enter=next) ----
  (function keyboardNav(){
    const rows = Array.from($table.querySelectorAll('tbody tr[data-sample-id]'));
    function nextInRow(inputs, el, dir){
      const idx = inputs.indexOf(el);
      const next = inputs[idx + dir] || (dir>0 ? inputs[0] : inputs[inputs.length-1]);
      return next;
    }
    $table.addEventListener('keydown', (ev)=>{
      const el = ev.target;
      if(!el.classList?.contains('form-input')) return;
      if(!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Enter'].includes(ev.key)) return;

      const row = el.closest('tr[data-sample-id]');
      const sid = row?.dataset.sampleId;
      const inputsRow = Array.from(row.querySelectorAll('.form-input'));
      let target = null;

      if (ev.key==='ArrowLeft')  target = nextInRow(inputsRow, el, -1);
      if (ev.key==='ArrowRight' || ev.key==='Enter') target = nextInRow(inputsRow, el, +1);
      if (ev.key==='ArrowUp' || ev.key==='ArrowDown'){
        const dir = ev.key==='ArrowDown' ? +1 : -1;
        const rowIdx = rows.indexOf(row);
        const row2 = rows[rowIdx + dir];
        if (row2){
          const idx = inputsRow.indexOf(el);
          const inputs2 = Array.from(row2.querySelectorAll('.form-input'));
          if (inputs2.length) target = inputs2[Math.min(idx, inputs2.length-1)];
        }
      }
      if (target){ ev.preventDefault(); target.focus(); target.select?.(); }
    });
  })();
})();
