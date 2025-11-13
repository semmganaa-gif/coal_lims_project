/* Solid (хатуугийн агуулага) — A/B/C загвар
   Формул: Solid% = C * 100 / (A - B)
   - Дүрэм: % 2 орон (ж. 27.14)
   - A−B ба % шууд realtime тооцогдоно
   - SAVE үед payload бэлдэж түгжинэ (ахлах буцаасан бол онгойно)
*/
(function () {
  const ANALYSIS_CODE = 'Solid';
  const TABLE_SEL = '#solid-analysis-table';
  const $table = document.querySelector(TABLE_SEL);
  if (!$table) return;

  // ----- storage helper (localStorage -> sessionStorage fallback)
  const storage = {
    set(k,v){ try{localStorage.setItem(k,String(v??''));}catch(e){} try{sessionStorage.setItem(k,String(v??''));}catch(e){} },
    get(k){ try{const v=localStorage.getItem(k); if(v!==null) return v;}catch(e){} try{const v2=sessionStorage.getItem(k); return v2??'';}catch(e){} return ''},
    del(k){ try{localStorage.removeItem(k);}catch(e){} try{sessionStorage.removeItem(k);}catch(e){} }
  };
  const K = (id)=> `analysis_${ANALYSIS_CODE}_${id}`;
  const REJECTED = window.REJECTED_SAMPLES || {};

  const num = (el) => {
    if(!el) return null;
    const s = String(el.value ?? '').trim().replace(',', '.');
    if (!s) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  };

  function refs(sampleId){
    const row = $table.querySelector(`tr[data-sample-id="${sampleId}"]`);
    if (!row) return null;
    return {
      row,
      A: row.querySelector(`#sample_${sampleId}_A`),
      B: row.querySelector(`#sample_${sampleId}_B`),
      AB: row.querySelector(`#sample_${sampleId}_AB`),
      C: row.querySelector(`#sample_${sampleId}_C`),
      pct: row.querySelector(`.solid-pct[data-sample-id="${sampleId}"]`)
    };
  }

  function fmt3(x){ return Number.isFinite(x) ? x.toFixed(3) : ''; }
  function fmt2(x){ return Number.isFinite(x) ? x.toFixed(2) : '-'; }

  // ---------- core
  function redraw(sampleId){
    const r = refs(sampleId);
    if (!r) return;

    const A = num(r.A), B = num(r.B), C = num(r.C);

    let wet = null, pct = null;
    if (A!=null && B!=null){
      wet = A - B;
      r.AB.value = fmt3(wet);
    } else {
      r.AB.value = '';
    }

    if (wet!=null && wet>0 && C!=null){
      pct = (C * 100.0) / wet;
      r.pct.textContent = fmt2(pct);
    } else {
      r.pct.textContent = '-';
    }
    return {A,B,wet,C,pct};
  }

  // ---------- public API (Save All дуудах хэлбэртэй адил)
  window.calculateAndDisplayForRow = function(sampleId, lock=false){
    const r = refs(sampleId);
    if (!r) return null;
    const calc = redraw(sampleId);

    if (!lock) return null;

    // final_result зөвхөн pct байгаа үед
    if (calc && Number.isFinite(calc.pct)){
      const isRejected = !!REJECTED[String(sampleId)];
      if (!isRejected){
        [r.A, r.B, r.C].forEach(inp=>{
          if (!inp) return;
          inp.readOnly = true;
          inp.classList.add('bg-light');
          storage.set(K(inp.id+'_locked'), 'true');
        });
      }

      return {
        sample_id: Number(sampleId),
        analysis_code: ANALYSIS_CODE,
        final_result: Number(calc.pct.toFixed(2)),
        raw_data: {
          A: Number.isFinite(calc.A)? +calc.A : null,
          B: Number.isFinite(calc.B)? +calc.B : null,
          wet_mass: Number.isFinite(calc.wet)? +Number(calc.wet.toFixed(3)) : null,
          C: Number.isFinite(calc.C)? +calc.C : null,
          solid_pct: +Number(calc.pct.toFixed(2))
        }
      };
    }
    return null;
  };

  // ---------- restore + input handlers
  document.addEventListener('DOMContentLoaded', ()=>{
    // restore inputs
    $table.querySelectorAll('tbody input.form-input').forEach(inp=>{
      const v = storage.get(K(inp.id));
      if (v!=='') inp.value = v;

      const sid = inp.closest('tr[data-sample-id]')?.dataset.sampleId;
      const isRejected = sid && REJECTED[String(sid)];
      const wasLocked  = storage.get(K(inp.id+'_locked'))==='true';
      if (isRejected){
        inp.readOnly = false; inp.classList.remove('bg-light');
        storage.del(K(inp.id+'_locked'));
      } else if (wasLocked){
        inp.readOnly = true; inp.classList.add('bg-light');
      }
    });

    // initial draw
    $table.querySelectorAll('tbody tr[data-sample-id]').forEach(tr=>{
      const sid = tr.dataset.sampleId;
      redraw(sid);
    });
  });

  $table.addEventListener('input', (e)=>{
    const el = e.target;
    if (!el.classList?.contains('form-input')) return;
    if (el.readOnly) return;

    storage.set(K(el.id), el.value ?? '');
    const sid = el.closest('tr[data-sample-id]')?.dataset.sampleId;
    if (sid) redraw(sid);
  });

  // keyboard nav (← → ↑ ↓ / Enter)
  (function keyboardNav(){
    const rows = Array.from($table.querySelectorAll('tbody tr[data-sample-id]'));
    $table.addEventListener('keydown', (ev)=>{
      const el = ev.target;
      if(!el.classList?.contains('form-input')) return;
      if(!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Enter'].includes(ev.key)) return;

      const row = el.closest('tr[data-sample-id]');
      const inputs = Array.from(row.querySelectorAll('.form-input'));
      const idx = inputs.indexOf(el);

      let target = null;
      if (ev.key==='ArrowLeft')  target = inputs[Math.max(0, idx-1)];
      if (ev.key==='ArrowRight' || ev.key==='Enter') target = inputs[Math.min(inputs.length-1, idx+1)];
      if (ev.key==='ArrowUp' || ev.key==='ArrowDown'){
        const dir = ev.key==='ArrowDown' ? +1 : -1;
        const rIdx = rows.indexOf(row);
        const row2 = rows[rIdx + dir];
        if (row2){
          const inputs2 = Array.from(row2.querySelectorAll('.form-input'));
          target = inputs2[Math.min(idx, inputs2.length-1)];
        }
      }
      if (target){ ev.preventDefault(); target.focus(); target.select?.(); }
    });
  })();
})();
