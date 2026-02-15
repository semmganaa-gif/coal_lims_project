/* static/js/calculators/mt_calculator.js
 * Нийт чийг (MT) – localStorage хадгалалт + найдвартай SAVE цуглуулалт
 */

(function () {
  // ---------- CONFIG ----------
  const TABLE_ID = '#total-moisture-analysis-table';

  // Анализын кодыг найдвартай авах (window -> data-attribute fallback)
  const TABLE_EL = document.querySelector(TABLE_ID);
  const ANALYSIS_CODE =
    (window.LIMS_ANALYSIS_CODE && String(window.LIMS_ANALYSIS_CODE)) ||
    (TABLE_EL && TABLE_EL.dataset.analysisCode) ||
    'MT';

const TOTAL_MOISTURE_REPEATABILITY_LIMIT = getRepeatabilityLimit('MT') ?? 0.5;
  const REJECTED_MAP = window.REJECTED_SAMPLES || {};

  // ---------- Storage helpers (localStorage) ----------
  const k = (id) => `analysis_${ANALYSIS_CODE}_${id}`;
  function sv(id, val) {
    try { localStorage.setItem(k(id), String(val ?? '')); } catch (e) {}
  }
  function gv(id) {
    try { const v = localStorage.getItem(k(id)); return v == null ? '' : v; }
    catch (e) { return ''; }
  }
  function rm(id) {
    try { localStorage.removeItem(k(id)); } catch (e) {}
  }

  // Коммад тэсвэртэй numeric parse
  const num = (s) => {
    if (s == null) return NaN;
    const v = Number(String(s).trim().replace(',', '.'));
    return Number.isFinite(v) ? v : NaN;
  };

  // ---------- Row calc ----------
  function calculateTotalMoistureForRow($row) {
    const m1Val = $row.find('input[id$="_m1"]').val();
    const m2Val = $row.find('input[id$="_m2"]').val();
    const m3Val = $row.find('input[id$="_m3"]').val();

    const m1 = num(m1Val);
    const m2_sample = num(m2Val);
    const m3_dish_dry = num(m3Val);

    let result = NaN;
    if (
      m1Val && m2Val && m3Val &&
      !Number.isNaN(m1) && !Number.isNaN(m2_sample) && !Number.isNaN(m3_dish_dry) &&
      m2_sample > 0
    ) {
      const wet_loss = (m1 + m2_sample) - m3_dish_dry;
      if (wet_loss >= 0) {
        result = (wet_loss / m2_sample) * 100;
      } else {
        console.warn('MT calc: m3 > m1+m2 ?', { m1, m2_sample, m3_dish_dry });
      }
    }

    return { result, m1, m2_sample, m3_dish_dry };
  }

  // ---------- Main per-row (payload when lockInputs=true) ----------
  window.calculateAndDisplayForRow = function (sampleId, lockInputs = false) {
    const $row1 = $(`${TABLE_ID} tr[data-sample-id="${sampleId}"][data-parallel="1"]`);
    const $row2 = $(`${TABLE_ID} tr[data-sample-id="${sampleId}"][data-parallel="2"]`);
    const $diffCell = $(`${TABLE_ID} .diff-cell[data-sample-id="${sampleId}"]`);
    const $avgCell  = $(`${TABLE_ID} .avg-cell[data-sample-id="${sampleId}"]`);

    if (!$row1.length) return null;

    const calc1 = calculateTotalMoistureForRow($row1);
    const calc2 = $row2.length ? calculateTotalMoistureForRow($row2) : { result: NaN };

    const res1 = calc1.result;
    const res2 = calc2.result;

    // UI
    $row1.find('.result-cell').text(!Number.isNaN(res1) ? res1.toFixed(2) : '-');
    if ($row2.length) $row2.find('.result-cell').text(!Number.isNaN(res2) ? res2.toFixed(2) : '-');

    let dataToSave = null;
    let avg = NaN, diff = NaN;

    if (!Number.isNaN(res1) && !Number.isNaN(res2)) {
      diff = Math.abs(res1 - res2);
      avg  = (res1 + res2) / 2;
      $diffCell.text(diff.toFixed(2));
      $avgCell.text(avg.toFixed(2));
      if (diff > TOTAL_MOISTURE_REPEATABILITY_LIMIT) {
        $diffCell.addClass('text-danger fw-bold').attr('title', `Tolerance exceeded! (Limit: ${TOTAL_MOISTURE_REPEATABILITY_LIMIT})`);
      } else {
        $diffCell.removeClass('text-danger fw-bold').addClass('text-success').attr('title', `OK (Limit: ${TOTAL_MOISTURE_REPEATABILITY_LIMIT})`);
      }
    } else if (!Number.isNaN(res1) && !$row2.length) {
      $diffCell.text('-').removeClass('text-success text-danger fw-bold').attr('title', '');
      avg = res1; $avgCell.text(avg.toFixed(2));
    } else {
      $diffCell.text('-').removeClass('text-success text-danger fw-bold').attr('title', '');
      $avgCell.text('-');
    }

    if (lockInputs) {
      if (!Number.isNaN(avg)) {
        const payload = {
          sample_id: Number(sampleId),
          analysis_code: ANALYSIS_CODE,
          final_result: Number(avg.toFixed(4)),
          raw_data: {
            p1: {
              dish_num: $row1.find('input[id$="_p1_num"]').val() || '',
              m1: Number.isFinite(calc1.m1) ? Number(calc1.m1.toFixed(4)) : null,
              m2_sample: Number.isFinite(calc1.m2_sample) ? Number(calc1.m2_sample.toFixed(4)) : null,
              m3_dish_dry: Number.isFinite(calc1.m3_dish_dry) ? Number(calc1.m3_dish_dry.toFixed(4)) : null,
              result: !Number.isNaN(res1) ? Number(res1.toFixed(4)) : null,
            },
            p2: {}
          }
        };
        if ($row2.length) {
          payload.raw_data.p2 = {
            dish_num: $row2.find('input[id$="_p2_num"]').val() || '',
            m1: Number.isFinite(calc2.m1) ? Number(calc2.m1.toFixed(4)) : null,
            m2_sample: Number.isFinite(calc2.m2_sample) ? Number(calc2.m2_sample.toFixed(4)) : null,
            m3_dish_dry: Number.isFinite(calc2.m3_dish_dry) ? Number(calc2.m3_dish_dry.toFixed(4)) : null,
            result: !Number.isNaN(res2) ? Number(res2.toFixed(4)) : null,
          };
          payload.raw_data.diff = Number.isFinite(diff) ? Number(diff.toFixed(4)) : null;
          payload.raw_data.limit_used = TOTAL_MOISTURE_REPEATABILITY_LIMIT;
        }
        payload.raw_data.avg = Number(avg.toFixed(4));

        // lock only if not rejected
        const isRejected = !!REJECTED_MAP[String(sampleId)];
        if (!isRejected) {
          const $inputsToLock = $row1.find('.form-input').add($row2.find('.form-input'));
          $inputsToLock.prop('readonly', true).addClass('bg-light');
          $inputsToLock.each(function () { sv($(this).attr('id') + '_locked', 'true'); });
        }
        return payload;
      }
      return null;
    }
    return null;
  };

  // ---------- PUBLIC: MT payload collector (SAVE-д хэрэглэнэ) ----------
  window.MT_collectPayload = function () {
    const payload = [];
    $(`${TABLE_ID} tbody tr[data-parallel="1"]`).each(function () {
      const sid = $(this).data('sample-id');
      const rowPayload = window.calculateAndDisplayForRow(sid, true); // <= чухал!
      if (rowPayload) payload.push(rowPayload);
    });
    return payload;
  };

  // ---------- DOM Ready: restore + persist ----------
  $(function () {
    // 1) restore
    const populated = new Set();
    $(`${TABLE_ID} tbody .form-input`).each(function () {
      const $inp = $(this);
      const id = $inp.attr('id');
      const sid = $inp.closest('tr[data-sample-id]').data('sample-id');
      const saved = gv(id);
      const isLocked = gv(id + '_locked') === 'true';
      const isRejected = !!REJECTED_MAP[String(sid)];

      if (saved !== '') { $inp.val(saved); if (sid) populated.add(sid); }

      if (isRejected) {
        $inp.prop('readonly', false).removeClass('bg-light');
        rm(id + '_locked');
      } else {
        if (isLocked) $inp.prop('readonly', true).addClass('bg-light');
        else $inp.prop('readonly', false).removeClass('bg-light');
      }
    });
    populated.forEach((sid) => { $(`.remove-sample-from-worksheet[data-sample-id="${sid}"]`).hide(); });

    // 2) draw locked summaries
    const locked = new Set();
    $(`${TABLE_ID} tbody tr[data-sample-id][data-parallel="1"]`).each(function () {
      const sid = $(this).data('sample-id');
      const firstId = $(this).find('.form-input:first').attr('id');
      const isRejected = !!REJECTED_MAP[String(sid)];
      if (!isRejected && firstId && gv(firstId + '_locked') === 'true') locked.add(sid);
    });
    locked.forEach((sid) => window.calculateAndDisplayForRow(sid, false));

    // 3) persist while typing (input + change)
    $(`${TABLE_ID} tbody`).on('input change', '.form-input', function () {
      const $inp = $(this);
      if ($inp.prop('readonly')) return;
      const id = $inp.attr('id');
      const val = $inp.val();
      const sid = $inp.closest('tr[data-sample-id]').data('sample-id');
      sv(id, val);

      // clear preview
      $(`${TABLE_ID} tr[data-sample-id="${sid}"] .result-cell`).text('-');
      $(`${TABLE_ID} .diff-cell[data-sample-id="${sid}"]`)
        .text('-').removeClass('text-success text-danger fw-bold').attr('title', '');
      $(`${TABLE_ID} .avg-cell[data-sample-id="${sid}"]`).text('-');

      $(`.remove-sample-from-worksheet[data-sample-id="${sid}"]`).show();
    });
  });
})();
