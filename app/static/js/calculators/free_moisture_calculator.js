/* static/js/calculators/FM_calculator.js
   FM (Free Moisture) — 3 жинтэй (tray/before/after).
   FM% = ((Wb - Wa) / (Wa - Wt)) * 100
   UI: Δ → 0.001 g, FM → 2 орон. SAVE үед түгжинэ (буцаасан бол онгойлгоно).
*/
(function () {
  const ANALYSIS_CODE = 'FM';
  const TABLE_SEL = '#free-moisture-analysis-table';
  const $table = document.querySelector(TABLE_SEL);
  if (!$table) return;

  const REJECTED_MAP = window.REJECTED_SAMPLES || {};
  const storage = {
    set(k, v){ try{ localStorage.setItem(k, String(v ?? '')); }catch(e){} try{ sessionStorage.setItem(k, String(v ?? '')); }catch(e){} },
    get(k){ try{ const v = localStorage.getItem(k); if(v!==null) return v; }catch(e){} try{ const v2 = sessionStorage.getItem(k); return v2??''; }catch(e){} return '' },
    del(k){ try{ localStorage.removeItem(k); }catch(e){} try{ sessionStorage.removeItem(k); }catch(e){} }
  };
  const K = (id)=> `analysis_${ANALYSIS_CODE}_${id}`;

  function num(el){
    if(!el) return null;
    const s = String(el.value ?? '').trim().replace(',', '.');
    if (!s) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  }

  function refs(sampleId){
    const row = $table.querySelector(`tr[data-sample-id="${sampleId}"]`);
    if (!row) return null;
    return {
      row,
      tray:   row.querySelector(`#sample_${sampleId}_tray`),
      before: row.querySelector(`#sample_${sampleId}_before`),
      after:  row.querySelector(`#sample_${sampleId}_after`),
      lossCell: row.querySelector('.loss-cell'),
      fmCell:   row.querySelector('.fm-cell')
    };
  }

  window.calculateAndDisplayForRow = function(sampleId, lockInputs=false){
    const r = refs(sampleId);
    if (!r) return null;

    const Wt = num(r.tray);
    const Wb = num(r.before);
    const Wa = num(r.after);

    let loss = null, fm = null;

    if (r.lossCell){ r.lossCell.textContent = '-'; r.lossCell.title = ''; }
    if (r.fmCell){   r.fmCell.textContent   = '-'; r.fmCell.classList.remove('text-danger','text-success'); r.fmCell.title=''; }

    if (Wb!=null && Wa!=null){
      loss = +(Wb - Wa);
      if (r.lossCell){
        r.lossCell.textContent = loss.toFixed(3);
        r.lossCell.title = 'Weight loss (g)';
      }
    }

    if (Wt!=null && Wb!=null && Wa!=null){
      const drySample = Wa - Wt;
      if (drySample > 0){
        fm = ((Wb - Wa) / drySample) * 100.0;
        if (Number.isFinite(fm) && r.fmCell){
          r.fmCell.textContent = fm.toFixed(2);
          r.fmCell.classList.add('text-success');
          r.fmCell.title = `FM = ((${Wb} - ${Wa}) / (${Wa} - ${Wt})) × 100`;
        }
      } else {
        if (r.fmCell){
          r.fmCell.textContent = '—';
          r.fmCell.classList.add('text-danger');
          r.fmCell.title = 'Denominator (after - tray) <= 0 — please check values.';
        }
      }
    }

    if (lockInputs && fm!=null){
      const isRejected = !!REJECTED_MAP[String(sampleId)];
      if (!isRejected){
        [r.tray, r.before, r.after].forEach(inp=>{
          if(!inp) return;
          inp.readOnly = true; inp.classList.add('bg-light');
          storage.set(K(inp.id+'_locked'), 'true');
        });
      }
      return {
        sample_id: Number(sampleId),
        analysis_code: ANALYSIS_CODE,
        final_result: +Number(fm.toFixed(4)),
        raw_data: {
          tray_g:   Number.isFinite(Wt)? +Number(Wt.toFixed(3)) : null,
          before_g: Number.isFinite(Wb)? +Number(Wb.toFixed(3)) : null,
          after_g:  Number.isFinite(Wa)? +Number(Wa.toFixed(3)) : null,
          loss_g:   Number.isFinite(loss)? +Number(loss.toFixed(3)) : null,
          formula: "FM% = ((Wb - Wa) / (Wa - Wt)) * 100"
        }
      };
    }
    return null;
  };

  function restoreInputs(){
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

    $table.querySelectorAll('tbody tr[data-sample-id]').forEach(tr=>{
      const sid = tr.dataset.sampleId;
      const anyInp = tr.querySelector('.form-input');
      const isRejected = !!REJECTED_MAP[String(sid)];
      if (anyInp && storage.get(K(anyInp.id+'_locked'))==='true' && !isRejected){
        window.calculateAndDisplayForRow(sid,false);
      }
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', restoreInputs, {once:true});
  } else {
    restoreInputs();
  }

  $table.addEventListener('input', (e)=>{
    const inp = e.target;
    if (!inp.classList.contains('form-input')) return;
    if (inp.readOnly) return;
    storage.set(K(inp.id), inp.value ?? '');

    const sid = inp.closest('tr[data-sample-id]')?.dataset.sampleId;
    if (!sid) return;
    const r = refs(sid);
    if (r){
      if (r.lossCell) { r.lossCell.textContent = '-'; r.lossCell.title=''; }
      if (r.fmCell){   r.fmCell.textContent   = '-'; r.fmCell.classList.remove('text-success','text-danger'); r.fmCell.title=''; }
    }
  });

  // Глобал сум/Enter навигац — давхцахгүй
  (function keyboardNavUniversal(){
    if (window.__LIMS_NAV_INSTALLED__) return;
    window.__LIMS_NAV_INSTALLED__ = true;

    const ROW_SEL = 'table[id$="-analysis-table"] tbody tr[data-sample-id]';

    function rowInputs(row){
      return Array.from(row.querySelectorAll('.form-input'))
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
      if (!(el instanceof HTMLInputElement) || !el.classList.contains('form-input')) return;

      const row = el.closest(ROW_SEL);
      if (!row) return;

      ev.preventDefault();
      ev.stopPropagation();

      const inputsRow = rowInputs(row);
      let target = null;

      if (ev.key === 'ArrowLeft')                    target = nextInRow(inputsRow, el, -1);
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
