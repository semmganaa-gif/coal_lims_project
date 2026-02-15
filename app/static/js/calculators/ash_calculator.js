/**
 * Үсний шинжилгээний тооцоологч модуль.
 * sessionStorage ашиглан утгуудыг түр хадгална.
 * "Хадгалах" үед input-үүдийг түгжинэ (readonly болгож, саарал фон тавина).
 * Гэхдээ: ахлахаас "засах" гэж буцаасан дээжүүдэд өмнөх түгжээг ҮГҮЙ гэж үзнэ.
 */

// --- ТОХИРГОО ---
const ANALYSIS_CODE = window.LIMS_ANALYSIS_CODE;          // analysis_page.html-ээс ирнэ
const TABLE_ID      = '#ash-analysis-table';              // энэ form-ын хүснэгт
const REJECTED_MAP  = window.REJECTED_SAMPLES || {};      // template-ээс ирнэ (sample_id -> info)
// --- /ТОХИРГОО ---

/** sessionStorage-д бичих */
function saveInputValue(inputId, value) {
    if (!ANALYSIS_CODE || ANALYSIS_CODE === 'window.LIMS_ANALYSIS_CODE') {
        console.error("saveInputValue: ANALYSIS_CODE тодорхойгүй эсвэл буруу тохирсон байна!");
        return;
    }
    try {
        sessionStorage.setItem(`analysis_${ANALYSIS_CODE}_${inputId}`, value);
    } catch (e) {
        console.error("sessionStorage хадгалах алдаа:", e);
    }
}
window.saveInputValue = saveInputValue;

/** sessionStorage-с унших */
function loadInputValue(inputId) {
    if (!ANАLYSIS_CODE || ANALYSIS_CODE === 'window.LIMS_ANALYSIS_CODE') {
        console.error("loadInputValue: ANALYSIS_CODE тодорхойгүй эсвэл буруу тохирсон байна!");
        return null;
    }
    return sessionStorage.getItem(`analysis_${ANALYSIS_CODE}_${inputId}`);
}
window.loadInputValue = loadInputValue;

/**
 * Нэг мөрний (p1 эсвэл p2) үнсний хувийг тооцоолно.
 */
function calculateAshForRow($row) {
    const m1Val = $row.find('input[id$="_m1"]').val();
    const m2Val = $row.find('input[id$="_m2"]').val();
    const m3Val = $row.find('input[id$="_m3"]').val();

    const m1        = parseFloat(m1Val);
    const m2_sample = parseFloat(m2Val);
    const m3_ashy   = parseFloat(m3Val);

    let result = NaN;
    if (m1Val && m2Val && m3Val &&
        !isNaN(m1) && !isNaN(m2_sample) && !isNaN(m3_ashy) &&
        m2_sample > 0) {
        result = ((m3_ashy - m1) / m2_sample) * 100;
        if (result < 0) result = 0;
    }

    return { result, m1, m2_sample, m3_ashy };
}

/**
 * Нэг дээжийг (хоёр параллельтэй) тооцоолж дэлгэцэнд харуулна.
 * lockInputs=true үед серверт өгөх object-ийг бэлдээд буцаана (inputs-ийг түгжинэ).
 */
function calculateAndDisplayForRow(sampleId, lockInputs = false) {
    const $row1    = $(`${TABLE_ID} tr[data-sample-id="${sampleId}"][data-parallel="1"]`);
    const $row2    = $(`${TABLE_ID} tr[data-sample-id="${sampleId}"][data-parallel="2"]`);
    const $diffCel = $(`${TABLE_ID} .diff-cell[data-sample-id="${sampleId}"]`);
    const $avgCel  = $(`${TABLE_ID} .avg-cell[data-sample-id="${sampleId}"]`);

    if (!$row1.length) {
        console.warn(`calculateAndDisplayForRow: row1 олдсонгүй (sample ${sampleId})`);
        return null;
    }

    const calc1 = calculateAshForRow($row1);
    const calc2 = $row2.length ? calculateAshForRow($row2) : { result: NaN };

    const res1 = calc1.result;
    const res2 = calc2.result;

    // Дэлгэцэнд
    $row1.find('.result-cell').text(!isNaN(res1) ? res1.toFixed(2) : '-');
    if ($row2.length) {
        $row2.find('.result-cell').text(!isNaN(res2) ? res2.toFixed(2) : '-');
    }

    let dataToSave = null;
    let avg = NaN;
    let diff = NaN;

    if (!isNaN(res1) && !isNaN(res2)) {
        diff = Math.abs(res1 - res2);
        avg  = (res1 + res2) / 2;

        $diffCel.text(diff.toFixed(2));
        $avgCel.text(avg.toFixed(2));

        // Динамик лимит (Aad T)
        let currentLimit = 0.3;
        if (avg < 15) currentLimit = 0.2;
        else if (avg <= 30) currentLimit = 0.3;
        else currentLimit = 0.5;

        if (diff > currentLimit) {
            $diffCel.addClass('text-danger fw-bold')
                    .attr('title', `Tolerance exceeded! (Limit: ${currentLimit})`);
        } else {
            $diffCel.removeClass('text-danger fw-bold')
                    .addClass('text-success')
                    .attr('title', `OK (Limit: ${currentLimit})`);
        }

    } else if (!isNaN(res1) && !$row2.length) {
        // Ганц параллель
        $diffCel.text('-').removeClass('text-success text-danger fw-bold').attr('title', '');
        avg = res1;
        $avgCel.text(avg.toFixed(2));
    } else {
        // Хоосон/алдаатай
        $diffCel.text('-').removeClass('text-success text-danger fw-bold').attr('title', '');
        $avgCel.text('-');
    }

    // Хадгалах үед
    if (lockInputs) {
        if (!isNaN(avg)) {
            // Серверт өгөх объект
            dataToSave = {
                sample_id: sampleId,
                analysis_code: ANALYSIS_CODE,
                final_result: avg.toFixed(4),
                raw_data: JSON.stringify({
                    p1: {
                        num: $row1.find('input[id$="_num"]').val(),
                        m1: calc1.m1,
                        m2_sample: calc1.m2_sample,
                        m3_ashy: calc1.m3_ashy,
                        result: !isNaN(res1) ? res1.toFixed(4) : null
                    },
                    p2: {
                        num: $row2.find('input[id$="_num"]').val(),
                        m1: calc2.m1,
                        m2_sample: calc2.m2_sample,
                        m3_ashy: calc2.m3_ashy,
                        result: !isNaN(res2) ? res2.toFixed(4) : null
                    },
                    diff: !isNaN(diff) ? diff.toFixed(4) : null,
                    avg: avg.toFixed(4)
                })
            };

            // ↪️ АНХНЫ ТӨЛӨВ: ахлахаас буцаасан байсан ч одоо химич ХАДГАЛЖ байгаа тул
            // энэ удаа түгжинэ. Тэгэхгүй бол хэн ч баталгаажуулах боломжгүй.
            const $inputsToLock = $row1.find('.form-input').add($row2.find('.form-input'));
            $inputsToLock.prop('readonly', true).addClass('bg-light');

            $inputsToLock.each(function () {
                saveInputValue($(this).attr('id') + '_locked', 'true');
            });
        } else {
            // Тооцоо гараагүй бол түгжихгүй
            dataToSave = null;
        }
    }

    return dataToSave;
}
window.calculateAndDisplayForRow = calculateAndDisplayForRow;

// --- DOM READY ---
$(function () {
    // Ash Calculator Script Initialization

    // Аль дээжийг 'утгатай' гэж үзэх вэ
    const populatedSampleIds = new Set();

    // Хүснэгт доторх бүх input-уудыг гүйж, sessionStorage-оос утга сэргээх
    $(`${TABLE_ID} tbody .form-input`).each(function () {
        const $input   = $(this);
        const inputId  = $input.attr('id');
        const $row     = $input.closest('tr[data-sample-id]');
        const sampleId = $row.data('sample-id');

        // Ахлахаас буцаасан эсэх
        const isRejected = REJECTED_MAP && REJECTED_MAP[String(sampleId)];

        const savedValue = loadInputValue(inputId);
        const isLocked   = loadInputValue(inputId + '_locked') === 'true';

        // 1) Утгыг нь сэргээнэ
        if (savedValue !== null && savedValue !== undefined && savedValue !== '') {
            $input.val(savedValue);
            if (sampleId) populatedSampleIds.add(sampleId);
        }

        // 2) Буцаасан дээж бол ТҮГЖИХГҮЙ, өмнөх *_locked-г цэвэрлэнэ
        if (isRejected) {
            // Өмнө нь түгжсэн байж болзошгүй тул хүчээр онгойлгоно
            $input.prop('readonly', false).removeClass('bg-light');

            // sessionStorage дахь түгжээг цэвэрлэнэ
            try {
                sessionStorage.removeItem(`analysis_${ANALYSIS_CODE}_${inputId}_locked`);
            } catch (e) {
                console.warn("Түгжээний flag-ийг storage-оос устгах боломжгүй:", e);
            }
        } else {
            // Энгийн үед түгжих эсэх
            if (isLocked) {
                $input.prop('readonly', true).addClass('bg-light');
            } else {
                $input.prop('readonly', false).removeClass('bg-light');
            }
        }
    });

    // Утгатай дээжүүдийн X товчийг нуух
    populatedSampleIds.forEach(sampleId => {
        $(`.remove-sample-from-worksheet[data-sample-id="${sampleId}"]`).hide();
    });

    // Хуудас ачаалахад түгжигдсэн мөрүүдийн дүнг харуулчих
    const lockedSampleIds = new Set();
    $(`${TABLE_ID} tbody tr[data-sample-id][data-parallel="1"]`).each(function () {
        const sampleId   = $(this).data('sample-id');
        const firstInput = $(this).find('.form-input:first').attr('id');

        const isRejected = REJECTED_MAP && REJECTED_MAP[String(sampleId)];
        if (isRejected) return; // буцаасан бол 'түгжигдсэн' мэт үзүүлэхгүй

        if (firstInput && loadInputValue(firstInput + '_locked') === 'true') {
            lockedSampleIds.add(sampleId);
        }
    });

    lockedSampleIds.forEach(sampleId => {
        window.calculateAndDisplayForRow(sampleId, false);
    });

    // Input өөрчлөгдөх бүрт: утгыг хадгалж, дүнгийн нүднүүдийг цэвэрлэнэ
    $(`${TABLE_ID} tbody`).on('input', '.form-input', function () {
        const $inp     = $(this);
        const inputId  = $inp.attr('id');
        const sampleId = $inp.closest('tr[data-sample-id]').data('sample-id');

        if (!$inp.prop('readonly')) {
            saveInputValue(inputId, $inp.val());

            // Дүнг цэвэрлэнэ → дараа нь "Хадгалах" дарвал шинээр тооцогдоно
            $(`${TABLE_ID} tr[data-sample-id="${sampleId}"] .result-cell`).text('-');
            $(`${TABLE_ID} .diff-cell[data-sample-id="${sampleId}"]`)
                .text('-')
                .removeClass('text-success text-danger fw-bold')
                .attr('title', '');
            $(`${TABLE_ID} .avg-cell[data-sample-id="${sampleId}"]`).text('-');

            // Давхар асуудал гарахгүйн тулд X товчийг харуулна
            $(`.remove-sample-from-worksheet[data-sample-id="${sampleId}"]`).show();
        }
    });

    // Ash Calculator Script Ready
});
