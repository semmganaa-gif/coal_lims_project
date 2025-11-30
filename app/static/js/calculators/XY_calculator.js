/* X + Y (нэг хуудсанд) — нэг мөрөөс хоёр кодын үр дүнг илгээнэ.
   Дэмжих селекторууд:
     #sample_{sid}_x_mm, #sample_{sid}_x, [name*="x" i], .x-input, [data-x], [data-code="X"]
     #sample_{sid}_y_mm, #sample_{sid}_y, [name*="y" i], .y-input, [data-y], [data-code="Y"]
   Хүснэгт: #xy-analysis-table
*/
(function(){
  const TABLE_SEL = '#xy-analysis-table';
  const PAGE_CODE = (window.LIMS_ANALYSIS_CODE_RAW || 'X');
  const REJECTED  = window.REJECTED_SAMPLES || {};
  const $table = document.querySelector(TABLE_SEL);
  if(!$table) return;

  const K = (id)=> `analysis_${PAGE_CODE}_${id}`;
  const storage = {
    set(k,v){ try{ localStorage.setItem(k,String(v??'')); }catch(e){} try{ sessionStorage.setItem(k,String(v??'')); }catch(e){} },
    get(k){ try{ const v=localStorage.getItem(k); if(v!==null) return v; }catch(e){} try{ const v2=sessionStorage.getItem(k); return v2??''; }catch(e){} return '' },
    del(k){ try{ localStorage.removeItem(k); }catch(e){} try{ sessionStorage.removeItem(k); }catch(e){} }
  };

  function num(el){
    if(!el) return null;
    const s = String(el.value ?? '').trim().replace(',', '.');
    if(!s) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  }

  function pickX(row, sid){
    return (
      row.querySelector(`#sample_${sid}_x_mm`) ||
      row.querySelector(`#sample_${sid}_x`) ||
      row.querySelector('[data-x]') ||
      row.querySelector('input[data-code="X"]') ||
      row.querySelector('.x-input') ||
      row.querySelector('[name*="x" i]')
    );
  }
  function pickY(row, sid){
    return (
      row.querySelector(`#sample_${sid}_y_mm`) ||
      row.querySelector(`#sample_${sid}_y`) ||
      row.querySelector('[data-y]') ||
      row.querySelector('input[data-code="Y"]') ||
      row.querySelector('.y-input') ||
      row.querySelector('[name*="y" i]')
    );
  }

  function refs(sid){
    const row = $table.querySelector(`tr[data-sample-id="${sid}"]`);
    if(!row) return null;

    // уян сонголт
    let x = pickX(row, sid);
    let y = pickY(row, sid);

    // fallback: мөрөн дэх идэвхтэй 2 input-ыг ашиглана (эхнийх=X, хоёрдох=Y)
    if(!x || !y){
      const inputs = Array.from(
        row.querySelectorAll('.form-input, input[type="number"], input[type="text"]')
      ).filter(i => !i.readOnly && !i.disabled);
      if(!x) x = inputs[0] || null;
      if(!y) y = inputs[1] || null;
    }

    return { row, x, y };
  }

  // --- НЭГ МӨРӨӨС 2 payload буцаана ---
  window.calculateAndDisplayForRow = function(sampleId, lockInputs=false){
    const r = refs(sampleId);
    if(!r) return null;

    const xVal = num(r.x);
    const yVal = num(r.y);

    const out = [];
    if(xVal!=null){
      out.push({
        sample_id: Number(sampleId),
        analysis_code: 'X',
        final_result: +Number(xVal.toFixed(2)),
        raw_data: { value_mm: +Number(xVal.toFixed(2)) }
      });
    }
    if(yVal!=null){
      out.push({
        sample_id: Number(sampleId),
        analysis_code: 'Y',
        final_result: +Number(yVal.toFixed(2)),
        raw_data: { value_mm: +Number(yVal.toFixed(2)) }
      });
    }

    if(!out.length) return null;

    // амжилттай тооцоолсон бол (буцаасан биш тохиолдолд) түгжинэ
    if(lockInputs && !REJECTED[String(sampleId)]){
      [r.x, r.y].forEach(inp=>{
        if(!inp) return;
        if(inp.value==='' || inp.readOnly) return;
        inp.readOnly = true;
        inp.classList.add('bg-light');
        storage.set(K(inp.id+'_locked'), 'true');
      });
    }

    return out; // массив
  };

  // --- Restore + typing persist ---
  function restore(){
    $table.querySelectorAll('tbody input').forEach(inp=>{
      const saved = storage.get(K(inp.id));
      if(saved !== '') inp.value = saved;

      const sid = inp.closest('tr[data-sample-id]')?.dataset.sampleId;
      const rejected = !!REJECTED[String(sid)];
      const wasLocked = storage.get(K(inp.id+'_locked'))==='true';

      if(rejected){
        inp.readOnly = false; inp.classList.remove('bg-light');
        storage.del(K(inp.id+'_locked'));
      }else if(wasLocked){
        inp.readOnly = true; inp.classList.add('bg-light');
      }
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', restore, {once:true});
  else restore();

  $table.addEventListener('input', (e)=>{
    const el = e.target;
    if(!(el instanceof HTMLInputElement)) return;
    if(el.readOnly) return;
    storage.set(K(el.id), el.value ?? '');
  });
})();
