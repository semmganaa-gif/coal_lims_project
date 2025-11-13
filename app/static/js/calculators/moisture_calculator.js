/**
 * Аналитик Чийг (Mad) тооцоолуур
 * - sessionStorage: түр хадгалалт
 * - "Хадгалах" үед л тооцоогоо баталгаажуулж (lock) серверт payload бэлдэнэ
 * - Ахлахаас "засах" болгосон (rejected) мөрүүдийг дахин онгойлгоно
 */

// --- ТОХИРГОО ---
const MOISTURE_REPEATABILITY_LIMIT = 0.2;       // T-limit
const ANALYSIS_CODE = window.LIMS_ANALYSIS_CODE;
const TABLE_ID = '#moisture-analysis-table';
const REJECTED_MAP = window.REJECTED_SAMPLES || {};
// --- /ТОХИРГОО ---

// -------------------- ТУСЛАХ --------------------
function saveInputValue(inputId, value) {
  if (!ANALYSIS_CODE || ANALYSIS_CODE === 'window.LIMS_ANALYSIS_CODE') {
    console.error('saveInputValue: ANALYSIS_CODE буруу!');
    return;
  }
  try { sessionStorage.setItem(`analysis_${ANALYSIS_CODE}_${inputId}`, value); }
  catch (e) { console.error('sessionStorage save error:', e); }
}
window.saveInputValue = saveInputValue;

function loadInputValue(inputId) {
  if (!ANALYSIS_CODE || ANALYSIS_CODE === 'window.LIMS_ANALYSIS_CODE') {
    console.error('loadInputValue: ANALYSIS_CODE буруу!');
    return null;
  }
  return sessionStorage.getItem(`analysis_${ANALYSIS_CODE}_${inputId}`);
}
window.loadInputValue = loadInputValue;

// Нэг мөрийн чийгийг тооцно
function calculateMoistureForRow($row) {
  const m1Val = $row.find('input[id$="_m1"]').val();        // хоосон бüks
  const m2Val = $row.find('input[id$="_m2"]').val();        // дээжийн жин
  const m3Val = $row.find('input[id$="_m3"]').val();        // хатаасан дээжтэй бüks

  const m1 = parseFloat(m1Val);
  const m2_sample = parseFloat(m2Val);
  const m3_dish_dry = parseFloat(m3Val);

  let result = NaN;

  if (
    m1Val && m2Val && m3Val &&
    Number.isFinite(m1) && Number.isFinite(m2_sample) && Number.isFinite(m3_dish_dry) &&
    m2_sample > 0
  ) {
    // ((m1 + m2) - m3) / m2 * 100
    const wet_weight_loss = (m1 + m2_sample) - m3_dish_dry;
    if (wet_weight_loss >= 0) {
      result = (wet_weight_loss / m2_sample) * 100;
    } else {
      console.warn('Mad: m3 > m1 + m2 ?', { m1, m2_sample, m3_dish_dry });
    }
  }

  return { result, m1, m2_sample, m3_dish_dry };
}

// -------------------- ГОЛ ФУНКЦ --------------------
window.calculateAndDisplayForRow = function (sampleId, lockInputs = false) {
  const $row1 = $(`${TABLE_ID} tr[data-sample-id="${sampleId}"][data-parallel="1"]`);
  const $row2 = $(`${TABLE_ID} tr[data-sample-id="${sampleId}"][data-parallel="2"]`);
  const $diffCell = $(`${TABLE_ID} .diff-cell[data-sample-id="${sampleId}"]`);
  const $avgCell = $(`${TABLE_ID} .avg-cell[data-sample-id="${sampleId}"]`);

  if (!$row1.length) {
    console.warn(`(Mad) row1 not found for sample ${sampleId}`);
    return null;
  }

  const calc1 = calculateMoistureForRow($row1);
  const calc2 = $row2.length ? calculateMoistureForRow($row2) : { result: NaN };

  const res1 = calc1.result;
  const res2 = calc2.result;

  // UI дээр харагдуулах
  $row1.find('.result-cell').text(Number.isFinite(res1) ? res1.toFixed(2) : '-');
  if ($row2.length) {
    $row2.find('.result-cell').text(Number.isFinite(res2) ? res2.toFixed(2) : '-');
  }

  let dataToSave = null;
  let avg = NaN;
  let diff = NaN;

  if (Number.isFinite(res1) && Number.isFinite(res2)) {
    // 2 параллел
    diff = Math.abs(res1 - res2);
    avg = (res1 + res2) / 2;
    $diffCell.text(diff.toFixed(2));
    $avgCell.text(avg.toFixed(2));

    if (diff > MOISTURE_REPEATABILITY_LIMIT) {
      $diffCell.addClass('text-danger fw-bold')
               .removeClass('text-success')
               .attr('title', `Тохиролц хэтэрсэн! (Limit: ${MOISTURE_REPEATABILITY_LIMIT})`);
    } else {
      $diffCell.removeClass('text-danger fw-bold')
               .addClass('text-success')
               .attr('title', `OK (Limit: ${MOISTURE_REPEATABILITY_LIMIT})`);
    }
  } else if (Number.isFinite(res1) && !$row2.length) {
    // ганц параллел
    $diffCell.text('-').removeClass('text-success text-danger fw-bold').attr('title', '');
    avg = res1;
    $avgCell.text(avg.toFixed(2));
  } else {
    // аль аль нь дутуу
    $diffCell.text('-').removeClass('text-success text-danger fw-bold').attr('title', '');
    $avgCell.text('-');
  }

  // ХАДГАЛАХ үед
  if (lockInputs) {
    if (Number.isFinite(avg)) {
      // серверт өгөх object (JSON.stringify хийхгүй)
      if (Number.isFinite(res1) && !$row2.length) {
        // ганц параллел
        dataToSave = {
          sample_id: Number(sampleId),
          analysis_code: ANALYSIS_CODE,
          final_result: Number(avg.toFixed(4)),
          raw_data: {
            p1: {
              bottle_num: $row1.find('input[id$="_p1_num"]').val() || '',
              m1: Number.isFinite(calc1.m1) ? Number(calc1.m1) : null,
              m2_sample: Number.isFinite(calc1.m2_sample) ? Number(calc1.m2_sample) : null,
              m3_dish_dry: Number.isFinite(calc1.m3_dish_dry) ? Number(calc1.m3_dish_dry) : null,
              result: Number.isFinite(res1) ? Number(res1.toFixed(4)) : null
            },
            p2: {},
            diff: null,
            avg: Number(avg.toFixed(4)),
            limit_used: MOISTURE_REPEATABILITY_LIMIT,
            limit_mode: "abs"
          }
        };
      } else {
        // 2 параллел
        dataToSave = {
          sample_id: Number(sampleId),
          analysis_code: ANALYSIS_CODE,
          final_result: Number(avg.toFixed(4)),
          raw_data: {
            p1: {
              bottle_num: $row1.find('input[id$="_p1_num"]').val() || '',
              m1: Number.isFinite(calc1.m1) ? Number(calc1.m1) : null,
              m2_sample: Number.isFinite(calc1.m2_sample) ? Number(calc1.m2_sample) : null,
              m3_dish_dry: Number.isFinite(calc1.m3_dish_dry) ? Number(calc1.m3_dish_dry) : null,
              result: Number.isFinite(res1) ? Number(res1.toFixed(4)) : null
            },
            p2: {
              bottle_num: $row2.find('input[id$="_p2_num"]').val() || '',
              m1: Number.isFinite(calc2.m1) ? Number(calc2.m1) : null,
              m2_sample: Number.isFinite(calc2.m2_sample) ? Number(calc2.m2_sample) : null,
              m3_dish_dry: Number.isFinite(calc2.m3_dish_dry) ? Number(calc2.m3_dish_dry) : null,
              result: Number.isFinite(res2) ? Number(res2.toFixed(4)) : null
            },
            diff: Number.isFinite(diff) ? Number(diff.toFixed(4)) : null,
            avg: Number(avg.toFixed(4)),
            limit_used: MOISTURE_REPEATABILITY_LIMIT,
            limit_mode: "abs"
          }
        };
      }

      // хадгалсан бол — инпутуудыг түгжинэ
      const $inputsToLock = $row1.find('.form-input').add($row2.find('.form-input'));
      $inputsToLock.prop('readonly', true).addClass('bg-light');
      $inputsToLock.each(function () {
        saveInputValue($(this).attr('id') + '_locked', 'true');
      });

    } else {
      // тооцоо гараагүй бол хадгалахгүй/түгжихгүй
      dataToSave = null;
    }
  }

  return dataToSave;
};

// -------------------- DOM READY --------------------
$(function () {
  console.log('Moisture Calculator Script Initializing...');

  // 1) sessionStorage-оос сэргээх
  const populatedSampleIds = new Set();

  $(`${TABLE_ID} tbody .form-input`).each(function () {
    const $input = $(this);
    const inputId = $input.attr('id');
    const $row = $input.closest('tr[data-sample-id]');
    const sampleId = $row.data('sample-id');

    const savedValue = loadInputValue(inputId);
    const isLocked = loadInputValue(inputId + '_locked') === 'true';
    const isRejected = !!(REJECTED_MAP && REJECTED_MAP[String(sampleId)]);

    if (savedValue !== null && savedValue !== undefined && savedValue !== '') {
      $input.val(savedValue);
      if (sampleId) populatedSampleIds.add(sampleId);
    }

    if (isRejected) {
      // Ахлахаас буцаасан → хүчээр онгойлгоно, lock flag-ийг цэвэрлэнэ
      $input.prop('readonly', false).removeClass('bg-light');
      try {
        sessionStorage.removeItem(`analysis_${ANALYSIS_CODE}_${inputId}_locked`);
      } catch (e) {
        console.warn('cannot remove locked flag for rejected sample:', e);
      }
    } else {
      // Энгийн тохиолдолд өмнөх lock-ийг хүндэтгэнэ
      if (isLocked) {
        $input.prop('readonly', true).addClass('bg-light');
      } else {
        $input.prop('readonly', false).removeClass('bg-light');
      }
    }
  });

  // 2) Утгатай мөрүүдийн X товчийг нуух
  populatedSampleIds.forEach((sampleId) => {
    $(`.remove-sample-from-worksheet[data-sample-id="${sampleId}"]`).hide();
  });

  // 3) Ачаалах үед түгжээтэй мөрүүдийн дүнг харуулах
  const lockedSampleIds = new Set();
  $(`${TABLE_ID} tbody tr[data-sample-id][data-parallel="1"]`).each(function () {
    const sampleId = $(this).data('sample-id');
    const firstInputId = $(this).find('.form-input:first').attr('id');
    const isRejected = !!(REJECTED_MAP && REJECTED_MAP[String(sampleId)]);
    if (isRejected) return;
    if (firstInputId && loadInputValue(firstInputId + '_locked') === 'true') {
      lockedSampleIds.add(sampleId);
    }
  });
  lockedSampleIds.forEach((sampleId) => {
    window.calculateAndDisplayForRow(sampleId, false);
  });

  // 4) Оролтын өөрчлөлт бүрт — түр хадгалж, UI-г цэвэрлэх
  $(`${TABLE_ID} tbody`).on('input', '.form-input', function () {
    const $inp = $(this);
    if ($inp.prop('readonly')) return;

    const inputId = $inp.attr('id');
    const val = $inp.val();
    const sampleId = $inp.closest('tr[data-sample-id]').data('sample-id');

    saveInputValue(inputId, val);

    // UI дээрх тооцоог цэвэрлэнэ (хадгалах дарсаны дараа шинэчлэгдэнэ)
    $(`${TABLE_ID} tr[data-sample-id="${sampleId}"] .result-cell`).text('-');
    $(`${TABLE_ID} .diff-cell[data-sample-id="${sampleId}"]`)
      .text('-')
      .removeClass('text-success text-danger fw-bold')
      .attr('title', '');
    $(`${TABLE_ID} .avg-cell[data-sample-id="${sampleId}"]`).text('-');

    // Одоо засвар хийж буй тул X товчийг буцааж харуулна
    $(`.remove-sample-from-worksheet[data-sample-id="${sampleId}"]`).show();
  });

  console.log('Moisture Calculator Script Ready.');
});
