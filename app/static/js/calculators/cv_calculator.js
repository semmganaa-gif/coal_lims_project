/* static/js/calculators/cv_calculator.js (SOP / ISO 1928:2020 стандартын дагуу нягталсан) */
(function () {
  const TABLE_ID = '#cv-analysis-table';
  const $tbl = document.querySelector(TABLE_ID);
  if (!$tbl) return;

  // --- Үндсэн тогтмолууд ---
  const J_PER_CAL = 4.1868;             // 1 cal = 4.1868 J
  const T_LIMIT   = 120;                // Зөвшөөрөгдөх тохирцын хязгаар (cal/g)
  
  // --- SOP 7.6.3 Тогтмолууд ---
  const S_CORR_FACTOR = 94.1;           // Хүхрийн засварын коэффициент (J / (%S * g))

  /**
   * SOP 7.6.3-ийн дагуу Азотын хүчлийн (α) коэффициентийг тооцоолно.
   * @param {number} Qb_Jg - Бомбын илчлэг (Qb), J/g нэгжээр
   * @returns {number} - Альфа (α) коэффициент
   */
  function getAlpha(Qb_Jg) {
    const Qb_MJkg = Qb_Jg / 1000.0; // J/g-г MJ/kg руу хөрвүүлэх (1 MJ/kg = 1000 J/g)
    
    if (Qb_MJkg <= 16.70) {
      return 0.0010;
    }
    if (Qb_MJkg <= 25.10) { // (16.70 < Qb <= 25.10)
      return 0.0012;
    }
    return 0.0016; // (Qb > 25.10)
  }

  // --- Хуудасны дээд талбараас утга авах функцууд ---
  const qE = () => num(document.getElementById('batch_calorific_system'));   // E (J/K)
  const q1 = () => num(document.getElementById('batch_fuse_correction'));    // q1 (J)
  const q2 = () => num(document.getElementById('batch_acid_correction'))||0; // q2 (J)

  /**
   * Input талбараас тоон утга унших
   * @param {HTMLElement} el - Input элемэнт
   * @returns {number|null} - Тоон утга эсвэл null
   */
  function num(el){
    if(!el) return null;
    const s = String(el.value ?? '').trim().replace(',', '.');
    if(!s) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  }

  /**
   * Тухайн мөрнөөс S (хүхэр)-ийн утгыг олно
   */
  function getS(sampleId, tr){
    const ds = tr?.dataset?.sadValue;
    if (ds !== undefined && ds !== '') {
      const n = Number(String(ds).replace(',', '.'));
      if (Number.isFinite(n)) return n;
    }
    const map = (window.S_BY_SAMPLE || {});
    if (map && map[sampleId] != null) {
      const n = Number(String(map[sampleId]).replace(',', '.'));
      if (Number.isFinite(n)) return n;
    }
    const ex = (window.EXISTING_RESULTS || {})[sampleId] || {};
    const cand = ex['St,ad'] ?? ex['TS'] ?? ex['TS,ad'] ?? ex['S'];
    if (cand != null) {
      const n = Number(String(cand).replace(',', '.'));
      if (Number.isFinite(n)) return n;
    }
    return null;
  }

  /**
   * SOP 7.6.2 болон 7.6.3 томьёоны дагуу нэг параллелийн илчлэгийг тооцоолно.
   */
  function calcOne(m, dT, E, q1_val, q2_val, S){
    // m, dT, E, q1, S заавал байх ёстой. q2 байхгүй бол 0.
    if (m==null || dT==null || E==null || q1_val==null || S==null) return null;
    
    // --- Үе шат 1: "Qb,ad" (SOP 7.6.2) ---
    // Qb = (E*Δt - q1 - q2) / m
    const Qb_Jg = ((E * dT) - q1_val - (q2_val || 0)) / m;
    
    // --- Үе шат 2: "Qgr,ad" (SOP 7.6.3) ---
    // Qgr,ad = Qb - (94.1 * S + α * Qb)
    const S_correction = S_CORR_FACTOR * S;
    const alpha = getAlpha(Qb_Jg);
    const acid_correction = alpha * Qb_Jg;
    const Qgr_ad_Jg = Qb_Jg - (S_correction + acid_correction);
    
    // --- Үе шат 3: cal/g руу хөрвүүлэх ---
    return Qgr_ad_Jg / J_PER_CAL; // cal/g
  }

  /**
   * Тухайн мөрний m, dT утгыг уншина.
   */
  function parseRow(sampleId, p){
    const m   = num(document.getElementById(`sample_${sampleId}_p${p}_m`));
    const dT  = num(document.getElementById(`sample_${sampleId}_p${p}_temp`));
    return {m, dT};
  }

  /**
   * (Global функц)
   * Дээжийн мөрөнд тооцоолол хийж, үр дүнг дэлгэцэнд харуулна.
   */
  window.calculateAndDisplayForRow = function(sampleId, lockInputs=false){
    const tr = $tbl.querySelector(`tr[data-sample-id="${sampleId}"]`);
    if (!tr) return null;

    // --- 1. Багцын тогтмол утгуудыг авах ---
    const E    = qE();
    const fuse = q1();
    const acid = q2();
    
    const res1Cell = tr.querySelector('.result-cell[data-parallel="1"]');
    const res2Cell = tr.querySelector('.result-cell[data-parallel="2"]');
    const diffCell = tr.querySelector('.diff-cell');
    const avgCell  = tr.querySelector('.avg-cell');
    const calcCell = tr.querySelector('.calc-cell');

    // --- 2. Шаардлагатай утгуудыг шалгах ---
    const S = getS(String(sampleId), tr);
    if (S==null){
      if (calcCell) calcCell.innerHTML = '<span class="text-danger">S (хүхэр) олдсонгүй</span>';
      if (res1Cell) res1Cell.textContent = '-';
      if (res2Cell) res2Cell.textContent = '-';
      if (diffCell){ diffCell.textContent='-'; diffCell.className='align-middle text-center diff-cell'; }
      if (avgCell) avgCell.textContent='-';
      return null; 
    } else {
      if (calcCell) calcCell.textContent = `S=${S.toFixed(2)}%`;
    }
    
    if (E == null || E <= 0) {
      if (calcCell) calcCell.innerHTML = '<span class="text-danger">E (багтаамж) оруулна уу</span>';
      return null;
    }

    if (fuse == null || fuse < 0) { // q1=0 байхыг зөвшөөрнө, гэхдээ null байж болохгүй
      if (calcCell) calcCell.innerHTML = '<span class="text-danger">q₁ (утас)-ын дулаан (J) оруулна уу</span>';
      return null;
    }

    // --- 3. Дээжийн мөрний утгуудыг авах ---
    const p1 = parseRow(sampleId, 1);
    const p2 = parseRow(sampleId, 2);

    // --- 4. Тооцоолол хийх (SOP-ийн дагуу) ---
    const r1 = calcOne(p1.m, p1.dT, E, fuse, acid, S);
    const r2 = calcOne(p2.m, p2.dT, E, fuse, acid, S);

    // --- 5. Үр дүнг дэлгэцэнд харуулах ---
    if (res1Cell) res1Cell.textContent = (r1!=null) ? r1.toFixed(2) : '-';
    if (res2Cell) res2Cell.textContent = (r2!=null) ? r2.toFixed(2) : '-';

    let avg = null, diff = null;

    if (r1!=null && r2!=null){
      avg  = (r1 + r2) / 2;
      diff = Math.abs(r1 - r2);
      if (diffCell){
        diffCell.textContent = diff.toFixed(2);
        diffCell.classList.remove('text-success','text-danger','fw-bold');
        if (diff > T_LIMIT){ diffCell.classList.add('text-danger','fw-bold'); }
        else { diffCell.classList.add('text-success'); }
      }
      if (avgCell) avgCell.textContent = avg.toFixed(2);
    } else if (r1!=null && r2==null){
      avg = r1;
      if (diffCell){ diffCell.textContent='-'; diffCell.className='align-middle text-center diff-cell'; }
      if (avgCell) avgCell.textContent = avg.toFixed(2);
    } else if (r1==null && r2!=null){
      avg = r2;
      if (diffCell){ diffCell.textContent='-'; diffCell.className='align-middle text-center diff-cell'; }
      if (avgCell) avgCell.textContent = avg.toFixed(2);
    } else {
      if (diffCell){ diffCell.textContent='-'; diffCell.className='align-middle text-center diff-cell'; }
      if (avgCell) avgCell.textContent='-';
      return null;
    }

    // --- 6. Хадгалах (lockInputs == true үед) ---
    if (lockInputs){
      tr.querySelectorAll('.form-input').forEach(inp=>{
        inp.readOnly = true; inp.classList.add('bg-light');
      });

      return {
        sample_id: Number(sampleId),
        analysis_code: 'CV',
        final_result: Number(avg.toFixed(4)),
        raw_data: {
          p1: { m:p1.m, dT:p1.dT, result: r1!=null? Number(r1.toFixed(4)) : null },
          p2: { m:p2.m, dT:p2.dT, result: r2!=null? Number(r2.toFixed(4)) : null },
          avg: Number(avg.toFixed(4)),
          diff: diff!=null? Number(diff.toFixed(4)) : null,
          E_used: E, 
          q1_used: fuse, 
          q2_used: acid,
          S_used: Number(S.toFixed(4)),
          limit_used: T_LIMIT
        }
      };
    }
    return null;
  };

  /**
   * Input-д өөрчлөлт орох бүрт хуучин үр дүнг цэвэрлэнэ.
   */
  $tbl.addEventListener('input', e=>{
    if(!e.target.classList.contains('form-input')) return;
    const tr = e.target.closest('tr[data-sample-id]');
    if(!tr) return;
    
    tr.querySelectorAll('.result-cell').forEach(n=>n.textContent='-');
    const d = tr.querySelector('.diff-cell'); if(d){ d.textContent='-'; d.className='align-middle text-center diff-cell'; }
    const a = tr.querySelector('.avg-cell');  if(a) a.textContent='-';
    
    const c = tr.querySelector('.calc-cell'); 
    if(c && c.querySelector('span.text-danger')) {
      const S = getS(String(tr.dataset.sampleId), tr);
      c.textContent = (S != null) ? `S=${S.toFixed(2)}%` : '-';
    }
  });

})();