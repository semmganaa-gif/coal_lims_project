/* CRI + CSR (нэг хуудсанд, параллель/дундажгүй, шууд оруулга)
   ─ Нэг мөрөөс 2 payload буцаана: {analysis_code:'CRI'},{analysis_code:'CSR'}
   ─ Дэмжих селекторууд:
       #sample_{sid}_cri, #sample_{sid}_csr
       [name*="cri" i], [name*="csr" i]
       .cri-input, .csr-input
       [data-cri], [data-csr], [data-code="CRI"], [data-code="CSR"]
     Fallback: мөрөн дэх эхний/хоёр дахь идэвхтэй input
   ─ Хүснэгт: #cricsr-analysis-table
*/
(function(){
  const TABLE_SEL = '#cricsr-analysis-table';
  const PAGE_CODE = (window.LIMS_ANALYSIS_CODE_RAW || 'CRI'); // route аль кодоор ч ирж болно
  const REJECTED  = window.REJECTED_SAMPLES || {};
  const $table = document.querySelector(TABLE_SEL);
  if(!$table) return;

  // Storage helpers (session→local тольддог)
  const K = (id)=> `analysis_${PAGE_CODE}_${id}`;
  const storage = {
    set(k,v){ try{ localStorage.setItem(k,String(v??'')); }catch(e){} try{ sessionStorage.setItem(k,String(v??'')); }catch(e){} },
    get(k){ try{ const v=localStorage.getItem(k); if(v!==null) return v; }catch(e){} try{ const v2=sessionStorage.getItem(k); return v2??''; }catch(e){} return '' },
    del(k){ try{ localStorage.removeItem(k); }catch(e){} try{ sessionStorage.removeItem(k); }catch(e){} }
  };

  // Комма→цэг & тоо болгон хувиргах
  function num(el){
    if(!el) return null;
    const s = String(el.value ?? '').trim().replace(',', '.');
    if(!s) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  }

  // Уян сонголтууд
  function pickCRI(row, sid){
    return (
      row.querySelector(`#sample_${sid}_cri`) ||
      row.querySelector('[data-cri]') ||
      row.querySelector('input[data-code="CRI"]') ||
      row.querySelector('.cri-input') ||
      row.querySelector('[name*="cri" i]')
    );
  }
  function pickCSR(row, sid){
    return (
      row.querySelector(`#sample_${sid}_csr`) ||
      row.querySelector('[data-csr]') ||
      row.querySelector('input[data-code="CSR"]') ||
      row.querySelector('.csr-input') ||
      row.querySelector('[name*="csr" i]')
    );
  }

  // Мөрийн reference-ууд
  function refs(sid){
    const row = $table.querySelector(`tr[data-sample-id="${sid}"]`);
    if(!row) return null;

    let cri = pickCRI(row, sid);
    let csr = pickCSR(row, sid);

    // Fallback: эхний хоёр идэвхтэй input (эхнийх=CRI, хоёрдох=CSR)
    if(!cri || !csr){
      const inputs = Array.from(
        row.querySelectorAll('.form-input, input[type="number"], input[type="text"]')
      ).filter(i => !i.readOnly && !i.disabled);
      if(!cri) cri = inputs[0] || null;
      if(!csr) csr = inputs[1] || null;
    }
    return { row, cri, csr };
  }

  // --- Нэг мөрийн тооцоо/цуглуулагч (хоёр payload буцаана) ---
  window.calculateAndDisplayForRow = function(sampleId, lockInputs=false){
    const r = refs(sampleId);
    if(!r) return null;

    const vCRI = num(r.cri);
    const vCSR = num(r.csr);

    const out = [];
    if(vCRI!=null){
      out.push({
        sample_id: Number(sampleId),
        analysis_code: 'CRI',
        final_result: +Number(vCRI.toFixed(2)),
        raw_data: { value: +Number(vCRI.toFixed(2)) }
      });
    }
    if(vCSR!=null){
      out.push({
        sample_id: Number(sampleId),
        analysis_code: 'CSR',
        final_result: +Number(vCSR.toFixed(2)),
        raw_data: { value: +Number(vCSR.toFixed(2)) }
      });
    }

    if(!out.length) return null;

    // Амжилттай SAVE үед түгжих (буцаасан бол түгжихгүй)
    if(lockInputs && !REJECTED[String(sampleId)]){
      [r.cri, r.csr].forEach(inp=>{
        if(!inp) return;
        if(inp.value==='' || inp.readOnly) return;
        inp.readOnly = true;
        inp.classList.add('bg-light');
        storage.set(K(inp.id+'_locked'), 'true');
      });
    }

    return out; // массив (2 хүртэл)
  };

  // --- Restore (утга/түгжээ) ---
  function restore(){
    $table.querySelectorAll('tbody input').forEach(inp=>{
      const saved = storage.get(K(inp.id));
      if(saved !== '') inp.value = saved;

      const sid = inp.closest('tr[data-sample-id]')?.dataset.sampleId;
      const isRejected = !!REJECTED[String(sid)];
      const wasLocked  = storage.get(K(inp.id+'_locked'))==='true';

      if(isRejected){
        inp.readOnly = false; inp.classList.remove('bg-light');
        storage.del(K(inp.id+'_locked'));
      }else if(wasLocked){
        inp.readOnly = true; inp.classList.add('bg-light');
      }
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', restore, {once:true});
  else restore();

  // Persist while typing
  $table.addEventListener('input', (e)=>{
    const el = e.target;
    if(!(el instanceof HTMLInputElement)) return;
    if(el.readOnly) return;
    storage.set(K(el.id), el.value ?? '');
  });
})();
