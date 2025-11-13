/* static/js/calculators/chlorine_calculator.js
   Chlorine (Cl,ad) — p1/p2 хувилбар, сервер дээр norm_code → 'Cl' болно. */
(function () {
  const ANALYSIS_CODE = 'Cl,ad';                 // API дээр norm_code → 'Cl'
  const TABLE_SEL = '#chlorine-analysis-table';
  const REPEATABILITY_LIMIT = 0.05;              // UI-д үзүүлэлт; сервер өөрийн дүрмээр дахин тооцно
  const REJECTED_MAP = window.REJECTED_SAMPLES || {};
  const $table = document.querySelector(TABLE_SEL);
  if (!$table) return;

  // ---------- Storage helpers ----------
  const storage = {
    set(k, v){ try{ localStorage.setItem(k, String(v ?? '')); }catch(e){} try{ sessionStorage.setItem(k, String(v ?? '')); }catch(e){} },
    get(k){ try{ const v = localStorage.getItem(k); if(v!==null) return v; }catch(e){} try{ const v2 = sessionStorage.getItem(k); return v2 ?? ''; }catch(e){} return '' },
    del(k){ try{ localStorage.removeItem(k); }catch(e){} try{ sessionStorage.removeItem(k); }catch(e){} }
  };
  const K = (id)=> `analysis_${ANALYSIS_CODE}_${id}`;

  // ---------- Utils ----------
  // comma → dot numeric parse
  function num(el){
    if(!el) return null;
    const s = String(el.value ?? '').trim().replace(',', '.');
    if(!s) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  }
  // мөрийн дотор шаардлагатай элементүүдийг авч ирнэ
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
      // ⬇️ зөвхөн тухайн мөрийн .diff/.avg/.calc нүд
      diff: row.querySelector('.diff-cell'),
      avg : row.querySelector('.avg-cell'),
      calc: row.querySelector('.calc-cell'),
    };
  }

  // ---------- Core calc + UI ----------
  window.calculateAndDisplayForRow = function(sampleId, lockInputs=false){
    const r = refs(sampleId);
    if (!r) return null;

    const p1w = num(r.p1.weight);
    const p2w = num(r.p2.weight);
    const p1r = num(r.p1.result);
    const p2r = num(r.p2.result);

    let avg=null, diff=null, t_exceeded=false;

    const resetUI = ()=>{
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
          r.diff.title = `T > ${REPEATABILITY_LIMIT} (хэтэрсэн)`;
        } else {
          r.diff.classList.add('text-success');
          r.diff.title = `T ≤ ${REPEATABILITY_LIMIT} (OK)`;
        }
      }
      if (r.avg)  r.avg.textContent  = avg.toFixed(3);
      if (r.calc) r.calc.innerHTML   = t_exceeded ? `<span class="text-warning">T хэтэрсэн</span>` : `<span class="text-success">OK</span>`;
    } else if (p1r!=null || p2r!=null){
      avg = (p1r!=null ? p1r : p2r);
      resetUI();
      if (r.avg) r.avg.textContent = avg.toFixed(3);
    } else {
      resetUI();
    }

    // Хадгалах payload + түгжих (буцаагдаагүй мөрүүдэд)
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
        analysis_code: ANALYSIS_CODE,                  // сервер дээр norm_code→'Cl'
        final_result: Number(avg.toFixed(4)),
        raw_data: {
          p1:   { weight: Number.isFinite(p1w)? +p1w : null, result: Number.isFinite(p1r)? +Number(p1r.toFixed(4)) : null },
          p2:   { weight: Number.isFinite(p2w)? +p2w : null, result: Number.isFinite(p2r)? +Number(p2r.toFixed(4)) : null },
          diff: Number.isFinite(diff)? +Number(diff.toFixed(4)) : null,
          avg:  +Number(avg.toFixed(4)),
          t_exceeded: !!t_exceeded,                    // UI-д мэдээлэл; сервер өөрөө дахин шалгана
          limit_used: REPEATABILITY_LIMIT,
          limit_mode: "abs"
        }
      };
    }
    return null;
  };

  // ---------- Restore (+ rejected unlock) ----------
  function restoreInputs(){
    $table.querySelectorAll('tbody input').forEach(inp=>{
      // зөвхөн анализын хүснэгтийн input-ууд
      if (!(inp instanceof HTMLInputElement)) return;

      // утга сэргээх
      const saved = storage.get(K(inp.id));
      if (saved !== '') inp.value = saved;

      // түгжээ сэргээх/нээх
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

    // Түгжээтэй мөрүүдийн preview-г сэргээе
    $table.querySelectorAll('tbody tr[data-sample-id]').forEach(tr=>{
      const sid = tr.dataset.sampleId;
      const anyInp = tr.querySelector('input');
      const isRejected = !!REJECTED_MAP[String(sid)];
      if (anyInp && storage.get(K(anyInp.id+'_locked'))==='true' && !isRejected){
        window.calculateAndDisplayForRow(sid,false);
      }
    });
  }

  // DOMContentLoaded дараа ажилладаг тохиолдолд: шууд init, эс тэгвээс listener
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', restoreInputs, {once:true});
  } else {
    restoreInputs();
  }

  // ---------- Persist on input + clear preview ----------
  $table.addEventListener('input', (e)=>{
    const inp = e.target;
    if (!(inp instanceof HTMLInputElement)) return;
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

  // ---------- Keyboard navigation (universal, давхар суулгахгүй) ----------
  (function keyboardNavUniversal(){
    if (window.__LIMS_NAV_INSTALLED__) return; // глобал нав байгаа бол дахин суулгахгүй
    const ROW_SEL = 'table[id$="-analysis-table"] tbody tr[data-sample-id]';

    function rowInputs(row){
      // Аль ч input (number/text), идэвхтэйгээс
      return Array.from(row.querySelectorAll('input[type="number"],input[type="text"]'))
        .filter(i => !i.readOnly && !i.disabled);
    }
    function nextInRow(inputs, el, dir){
      const idx = inputs.indexOf(el);
      if (idx < 0) return inputs[0] || null;
      const n = inputs[idx + dir];
      return n || (dir > 0 ? inputs[0] : inputs[inputs.length - 1]) || null;
    }

    document.addEventListener('keydown', function(ev){
      const keys = ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Enter'];
      if (!keys.includes(ev.key)) return;

      const el = ev.target;
      if (!(el instanceof HTMLInputElement)) return;
      if (!el.closest('table[id$="-analysis-table"]')) return;

      const row = el.closest(ROW_SEL);
      if (!row) return;

      // number input-ийн default increment-ийг тасалж, өөрсдөө шилжүүлнэ
      ev.preventDefault();
      ev.stopPropagation();

      const inputsRow = rowInputs(row);
      let target = null;

      if (ev.key === 'ArrowLeft')                  target = nextInRow(inputsRow, el, -1);
      if (ev.key === 'ArrowRight' || ev.key === 'Enter') target = nextInRow(inputsRow, el, +1);

      if (ev.key === 'ArrowUp' || ev.key === 'ArrowDown'){
        const allRows = Array.from(document.querySelectorAll(ROW_SEL));
        const rowIdx  = allRows.indexOf(row);
        const row2    = allRows[rowIdx + (ev.key === 'ArrowDown' ? +1 : -1)];
        if (row2){
          const idx = Math.max(0, inputsRow.indexOf(el));
          const inputs2 = rowInputs(row2);
          if (inputs2.length) target = inputs2[Math.min(idx, inputs2.length - 1)];
        }
      }

      if (target){ target.focus(); target.select?.(); }
    }, true);
  })();

})();
