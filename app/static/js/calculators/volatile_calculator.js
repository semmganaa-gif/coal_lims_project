/**
 * Дэгдэмхий бодис (Vad) шинжилгээний тооцоологч модуль.
 * - sessionStorage ашиглана
 * - зөвхөн "Хадгалах" үед түгжинэ
 * - Mad-ыг data-attribute-ээс уншина
 * - Ахлахаас буцаасан мөрийг дахин онгойлгох боломжтой болгосон
 */

// --- ТОХИРГОО ---
const VOLATILE_REPEATABILITY_LIMIT = getRepeatabilityLimit('Vad') ?? 0.5;
const ANALYSIS_CODE = window.LIMS_ANALYSIS_CODE;
const TABLE_ID = '#volatile-analysis-table';
// ⬇️ ШИНЭ: ахлахаас буцаасан жагсаалт
const REJECTED_MAP = window.REJECTED_SAMPLES || {};
// --- /ТОХИРГОО ---

// --- ГЛОБАЛ туслахууд ---
window.saveInputValue = function (inputId, value) {
  if (!ANALYSIS_CODE || ANALYSIS_CODE === 'window.LIMS_ANALYSIS_CODE') {
    console.error('saveInputValue: ANALYSIS_CODE алга эсвэл буруу байна!');
    return;
  }
  try {
    sessionStorage.setItem(`analysis_${ANALYSIS_CODE}_${inputId}`, value);
  } catch (e) {
    console.error(`SessionStorage хадгалах алдаа (${ANАЛYSIS_CODE}, ${inputId}):`, e);
  }
};

window.loadInputValue = function (inputId) {
  if (!ANАЛYSIS_CODE || ANALYSIS_CODE === 'window.LIMS_ANALYSIS_CODE') {
    console.error('loadInputValue: ANALYSIS_CODE алга эсвэл буруу байна!');
    return null;
  }
  return sessionStorage.getItem(`analysis_${ANАЛYSIS_CODE}_${inputId}`);
};

// --- Нэг мөр тооцоолох ---
function calculateVolatileForRow(row) {
  const m1Val = row.find('input[id$="_m1"]').val();
  const m2Val = row.find('input[id$="_m2"]').val();
  const m3Val = row.find('input[id$="_m3"]').val();

  const m1 = parseFloat(m1Val);
  const m2_sample = parseFloat(m2Val);
  const m3_residue = parseFloat(m3Val);

  const sampleId = row.data('sample-id');
  const $row1 = $(
    `${TABLE_ID} tr[data-sample-id="${sampleId}"][data-parallel="1"]`
  );
  const madVal = $row1.data('mad-value');
  const mad = parseFloat(madVal);

  let result = NaN;

  if (isNaN(mad)) {
    console.warn(
      `Sample ID ${sampleId}: Mad утга байхгүй эсвэл тоо биш ('${madVal}').`
    );
  } else if (
    m1Val &&
    m2Val &&
    m3Val &&
    !isNaN(m1) &&
    !isNaN(m2_sample) &&
    !isNaN(m3_residue) &&
    m2_sample > 0
  ) {
    // Vad = (((m1 + m2) - m3) / m2) * 100 - Mad
    const weight_loss = m1 + m2_sample - m3_residue;
    if (weight_loss >= 0) {
      result = (weight_loss / m2_sample) * 100 - mad;
      if (result < 0) result = 0;
    } else {
      console.warn('Vad тооцоо: үлдэгдэл (m3) > m1 + m2 ?', {
        m1,
        m2_sample,
        m3_residue,
      });
    }
  }

  return {
    result,
    m1,
    m2_sample,
    m3_residue,
    mad,
  };
}

// --- Гол функц ---
window.calculateAndDisplayForRow = function (sampleId, lockInputs = false) {
  const $row1 = $(
    `${TABLE_ID} tr[data-sample-id="${sampleId}"][data-parallel="1"]`
  );
  const $row2 = $(
    `${TABLE_ID} tr[data-sample-id="${sampleId}"][data-parallel="2"]`
  );
  const $diffCell = $(
    `${TABLE_ID} .diff-cell[data-sample-id="${sampleId}"]`
  );
  const $avgCell = $(`${TABLE_ID} .avg-cell[data-sample-id="${sampleId}"]`);

  if (!$row1.length) {
    console.warn(`calculateAndDisplayForRow (Vad): 1-р мөр олдсонгүй (sample ${sampleId})`);
    return null;
  }

  const calc1 = calculateVolatileForRow($row1);
  const calc2 = $row2.length
    ? calculateVolatileForRow($row2)
    : { result: NaN, mad: calc1.mad };

  const res1 = calc1.result;
  const res2 = calc2.result;
  const madUsed = calc1.mad;

  // Mad байхгүй бол хадгалж болохгүй
  if (isNaN(madUsed)) {
    $row1.find('.result-cell').text('Mad алга!').addClass('text-danger');
    if ($row2.length) {
      $row2.find('.result-cell').text('Mad алга!').addClass('text-danger');
    }
    $diffCell.text('-').removeClass('text-success text-danger fw-bold');
    $avgCell.text('-');
    return null;
  }

  // Дэлгэцэнд харуулах
  $row1.find('.result-cell').text(!isNaN(res1) ? res1.toFixed(2) : '-').removeClass('text-danger');
  if ($row2.length) {
    $row2
      .find('.result-cell')
      .text(!isNaN(res2) ? res2.toFixed(2) : '-')
      .removeClass('text-danger');
  }

  let dataToSave = null;
  let avg = NaN;
  let diff = NaN;

  if (!isNaN(res1) && !isNaN(res2)) {
    // хоёр параллел
    diff = Math.abs(res1 - res2);
    avg = (res1 + res2) / 2;
    $diffCell.text(diff.toFixed(2));
    $avgCell.text(avg.toFixed(2));

    if (diff > VOLATILE_REPEATABILITY_LIMIT) {
      $diffCell
        .removeClass('text-success')
        .addClass('text-danger fw-bold')
        .attr(
          'title',
          `Зөвшөөрөгдөх хязгаараас (${VOLATILE_REPEATABILITY_LIMIT}) хэтэрсэн!`
        );
    } else {
      $diffCell
        .removeClass('text-danger fw-bold')
        .addClass('text-success')
        .attr('title', `Зөвшөөрөгдөх хязгаар: ${VOLATILE_REPEATABILITY_LIMIT}`);
    }
  } else if (!isNaN(res1) && !$row2.length) {
    // ганц параллел
    $diffCell
      .text('-')
      .removeClass('text-success text-danger fw-bold')
      .attr('title', '');
    avg = res1;
    $avgCell.text(avg.toFixed(2));
  } else {
    // дутуу
    $diffCell.text('-').removeClass('text-success text-danger fw-bold').attr('title', '');
    $avgCell.text('-');
  }

  // Хадгалах үед
  if (lockInputs) {
    if (!isNaN(avg)) {
      // хадгалах object
      if (!isNaN(res1) && !$row2.length) {
        // ганц параллел
        dataToSave = {
          sample_id: sampleId,
          analysis_code: ANALYSIS_CODE,
          final_result: avg.toFixed(4),
          raw_data: JSON.stringify({
            p1: {
              num: $row1.find('input[id$="_p1_num"]').val(),
              m1: !isNaN(calc1.m1) ? calc1.m1.toFixed(4) : null,
              m2_sample: !isNaN(calc1.m2_sample) ? calc1.m2_sample.toFixed(4) : null,
              m3_residue: !isNaN(calc1.m3_residue)
                ? calc1.m3_residue.toFixed(4)
                : null,
              result: res1.toFixed(4),
            },
            p2: {},
            diff: null,
            avg: avg.toFixed(4),
            mad_used: madUsed.toFixed(4),
          }),
        };
      } else {
        // хоёр параллел
        dataToSave = {
          sample_id: sampleId,
          analysis_code: ANALYSIS_CODE,
          final_result: avg.toFixed(4),
          raw_data: JSON.stringify({
            p1: {
              num: $row1.find('input[id$="_p1_num"]').val(),
              m1: !isNaN(calc1.m1) ? calc1.m1.toFixed(4) : null,
              m2_sample: !isNaN(calc1.m2_sample) ? calc1.m2_sample.toFixed(4) : null,
              m3_residue: !isNaN(calc1.m3_residue)
                ? calc1.m3_residue.toFixed(4)
                : null,
              result: !isNaN(res1) ? res1.toFixed(4) : null,
            },
            p2: {
              num: $row2.find('input[id$="_p2_num"]').val(),
              m1: !isNaN(calc2.m1) ? calc2.m1.toFixed(4) : null,
              m2_sample: !isNaN(calc2.m2_sample) ? calc2.m2_sample.toFixed(4) : null,
              m3_residue: !isNaN(calc2.m3_residue)
                ? calc2.m3_residue.toFixed(4)
                : null,
              result: !isNaN(res2) ? res2.toFixed(4) : null,
            },
            diff: !isNaN(diff) ? diff.toFixed(4) : null,
            avg: avg.toFixed(4),
            mad_used: madUsed.toFixed(4),
            limit_used: VOLATILE_REPEATABILITY_LIMIT,
          }),
        };
      }

      // амжилттай бол цоожлоно
      const $inputsToLock = $row1.find('.form-input').add($row2.find('.form-input'));
      $inputsToLock.prop('readonly', true).addClass('bg-light');
      $inputsToLock.each(function () {
        saveInputValue($(this).attr('id') + '_locked', 'true');
      });
      // Sample locked (removed log for production)
    } else {
      // Sample not locked (removed log for production)
      dataToSave = null;
    }
  }

  return dataToSave;
};

// --- DOM READY ---
$(function () {
  // Removed console.log for production

  const populatedSampleIds = new Set();

  // 1. input-уудыг сэргээх
  $(`${TABLE_ID} tbody .form-input`).each(function () {
    const $input = $(this);
    const inputId = $input.attr('id');
    const sampleId = $input.closest('tr[data-sample-id]').data('sample-id');
    const savedValue = loadInputValue(inputId);
    const isLocked = loadInputValue(inputId + '_locked') === 'true';
    const isRejected = REJECTED_MAP && REJECTED_MAP[String(sampleId)];

    // өмнө нь утга байсан бол тавина
    if (savedValue !== null && savedValue !== undefined && savedValue !== '') {
      $input.val(savedValue);
      if (sampleId) populatedSampleIds.add(sampleId);
    }

    if (isRejected) {
      // ⬇️ ШИНЭ: ахлахаас "засах" гэж буцаасан → түгжээг тайлна
      $input.prop('readonly', false).removeClass('bg-light');
      try {
        sessionStorage.removeItem(`analysis_${ANАЛYSIS_CODE}_${inputId}_locked`);
      } catch (e) {
        console.warn('Буцаасан Vad дээжийн түгжээг storage-оос арилгах боломжгүй:', e);
      }
      // Дахин засч байгаагаар X товчийг доор харуулна
    } else {
      // энгийн логик
      if (isLocked) {
        $input.prop('readonly', true).addClass('bg-light');
      } else {
        $input.prop('readonly', false).removeClass('bg-light');
      }
    }
  });

  // 2. утгатай байсан дээж → X товчийг нуух (буцаасан бол харуулна)
  // Hiding X button for populated samples (removed log for production)
  populatedSampleIds.forEach((sampleId) => {
    if (REJECTED_MAP && REJECTED_MAP[String(sampleId)]) {
      $(`.remove-sample-from-worksheet[data-sample-id="${sampleId}"]`).show();
    } else {
      $(`.remove-sample-from-worksheet[data-sample-id="${sampleId}"]`).hide();
    }
  });

  // 3. ачаалахад түгжигдсэн мөрүүдийг дахин зурна
  const lockedSampleIds = new Set();
  $(`${TABLE_ID} tbody tr[data-sample-id][data-parallel="1"]`).each(function () {
    const sampleId = $(this).data('sample-id');
    const firstInputId = $(this).find('.form-input:first').attr('id');
    const isRejected = REJECTED_MAP && REJECTED_MAP[String(sampleId)];
    if (isRejected) return; // буцаасан бол "түгжигдсэн" гэж тооцохгүй
    if (firstInputId && loadInputValue(firstInputId + '_locked') === 'true') {
      lockedSampleIds.add(sampleId);
    }
  });
  lockedSampleIds.forEach((sampleId) => {
    window.calculateAndDisplayForRow(sampleId, false);
  });

  // 4. input дээр бичихэд хадгалах + тооцоог цэвэрлэх
  $(`${TABLE_ID} tbody`).on('input', '.form-input', function () {
    if (!$(this).prop('readonly')) {
      const inputId = $(this).attr('id');
      const sampleId = $(this).closest('tr[data-sample-id]').data('sample-id');
      const val = $(this).val();

      saveInputValue(inputId, val);

      // тооцоог цэвэрлэнэ
      $(`${TABLE_ID} tr[data-sample-id="${sampleId}"] .result-cell`)
        .text('-')
        .removeClass('text-danger');
      $(`${TABLE_ID} .diff-cell[data-sample-id="${sampleId}"]`)
        .text('-')
        .removeClass('text-success text-danger fw-bold')
        .attr('title', '');
      $(`${TABLE_ID} .avg-cell[data-sample-id="${sampleId}"]`).text('-');

      // одоо засаж байгаа тул X товчийг харуулна
      $(`.remove-sample-from-worksheet[data-sample-id="${sampleId}"]`).show();
    }
  });

  // Removed console.log for production
});
