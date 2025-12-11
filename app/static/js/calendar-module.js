/**
 * calendar-module.js - Нийтлэг Calendar Module
 * 7 хоногийн rolling calendar
 *
 * Usage:
 *   // HTML-д script оруулах (base.html-д):
 *   <script src="{{ url_for('static', filename='js/calendar-module.js') }}"></script>
 *
 *   // JS-д ашиглах:
 *   CalendarModule.buildCalendar('containerId', 'labelId', centerDate, selectedStr, onSelectCallback);
 *   CalendarModule.formatISO(date);
 *   CalendarModule.parseDate('2025-01-15');
 */

const CalendarModule = (function() {
  'use strict';

  // Монгол сарын нэрс
  const MONTH_NAMES = [
    "1-р сар", "2-р сар", "3-р сар", "4-р сар", "5-р сар", "6-р сар",
    "7-р сар", "8-р сар", "9-р сар", "10-р сар", "11-р сар", "12-р сар"
  ];

  // Долоо хоногийн өдрүүд
  const WEEK_DAYS = ["Ня", "Да", "Мя", "Лх", "Пү", "Ба", "Бя"];

  /**
   * Сарын нэр + жил форматлах
   * @param {Date} date
   * @returns {string} "1-р сар 2025"
   */
  function formatDateLabel(date) {
    if (!(date instanceof Date) || isNaN(date)) return '---';
    return MONTH_NAMES[date.getMonth()] + " " + date.getFullYear();
  }

  /**
   * String-ээс Date object үүсгэх
   * @param {string} str - "YYYY-MM-DD" format
   * @returns {Date}
   */
  function parseDate(str) {
    if (!str) return new Date();
    try {
      // ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:mm
      const datePart = str.split('T')[0];
      const parts = datePart.split('-');
      if (parts.length === 3) {
        return new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
      }
      return new Date(str);
    } catch (e) {
      console.warn('CalendarModule: Date parse error:', e);
      return new Date();
    }
  }

  /**
   * Date object-ийг ISO format болгох
   * @param {Date} date
   * @returns {string} "YYYY-MM-DD"
   */
  function formatISO(date) {
    if (!(date instanceof Date) || isNaN(date)) return '';
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }

  /**
   * Date object-ийг datetime-local input format болгох
   * @param {Date} date
   * @returns {string} "YYYY-MM-DDTHH:mm"
   */
  function formatLocalDateTime(date) {
    if (!(date instanceof Date) || isNaN(date)) return '';
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    const h = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${d}T${h}:${min}`;
  }

  /**
   * 7 хоногийн rolling calendar үүсгэх
   * @param {string} containerId - Calendar table container element ID
   * @param {string} labelId - Month/year label element ID
   * @param {Date} centerDate - Дундаж огноо (энэ өдрийн эргэн тойрон 3 өдөр)
   * @param {string} selectedStr - Сонгогдсон огноо (YYYY-MM-DD эсвэл YYYY-MM-DDTHH:mm)
   * @param {function} onSelect - Огноо сонгоход дуудагдах callback (isoDate параметртэй)
   * @param {object} options - Нэмэлт тохиргоо { appendTime: 'T00:00' | 'T23:59' | null }
   */
  function buildCalendar(containerId, labelId, centerDate, selectedStr, onSelect, options = {}) {
    const container = document.getElementById(containerId);
    const label = document.getElementById(labelId);

    if (!container) {
      console.warn('CalendarModule: Container not found:', containerId);
      return;
    }

    container.innerHTML = '';

    if (label) {
      label.textContent = formatDateLabel(centerDate);
    }

    // 3 өдрийн өмнөөс эхлэх
    const startDate = new Date(centerDate);
    startDate.setDate(centerDate.getDate() - 3);

    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');
    const trHead = document.createElement('tr');
    const trBody = document.createElement('tr');

    // Selected date-ийг ISO format болгох (хугацааг хасах)
    const selectedISO = selectedStr ? selectedStr.split('T')[0] : '';

    for (let i = 0; i < 7; i++) {
      const currentDate = new Date(startDate);
      currentDate.setDate(startDate.getDate() + i);

      const dayNum = currentDate.getDate();
      const isoDate = formatISO(currentDate);

      // Header (weekday)
      const th = document.createElement('th');
      th.textContent = WEEK_DAYS[currentDate.getDay()];
      trHead.appendChild(th);

      // Body (day number)
      const td = document.createElement('td');
      td.textContent = dayNum;
      td.className = 'calendar-day';

      // Өнөөдөр эсэхийг шалгах
      const today = new Date();
      if (formatISO(currentDate) === formatISO(today)) {
        td.classList.add('today');
      }

      // Сонгогдсон эсэх
      if (selectedISO === isoDate) {
        td.classList.add('selected');
      }

      // Click handler
      td.addEventListener('click', function() {
        if (typeof onSelect === 'function') {
          // appendTime option байвал цаг нэмэх
          const result = options.appendTime ? isoDate + options.appendTime : isoDate;
          onSelect(result);
        }
        buildCalendar(containerId, labelId, currentDate, isoDate, onSelect, options);
      });

      trBody.appendChild(td);
    }

    thead.appendChild(trHead);
    tbody.appendChild(trBody);
    container.appendChild(thead);
    container.appendChild(tbody);
  }

  /**
   * Calendar navigation (prev/next week)
   * @param {Date} centerDate - Одоогийн дунд огноо (mutate хийгдэнэ!)
   * @param {number} direction - -1 (өмнөх долоо хоног) эсвэл 1 (дараагийн)
   * @param {function} renderCallback - Calendar дахин render хийх callback
   */
  function navigate(centerDate, direction, renderCallback) {
    const shiftDays = 7 * direction;
    centerDate.setDate(centerDate.getDate() + shiftDays);
    if (typeof renderCallback === 'function') {
      renderCallback();
    }
  }

  /**
   * Ээлжийн default эхлэх/дуусах огноо тооцох
   * 06:00-05:59 ээлжийн дагуу
   * @returns {{ start: Date, end: Date }}
   */
  function getShiftDefaults() {
    const now = new Date();
    const start = new Date(now);
    const end = new Date(now);

    if (now.getHours() < 6) {
      // Өглөө 6 цагаас өмнө → өчигдрийн ээлж
      start.setDate(start.getDate() - 1);
      start.setHours(6, 0, 0, 0);
      end.setHours(5, 59, 0, 0);
    } else {
      // Өглөө 6 цагаас хойш → өнөөдрийн ээлж
      start.setHours(6, 0, 0, 0);
      end.setDate(end.getDate() + 1);
      end.setHours(5, 59, 0, 0);
    }

    return { start, end };
  }

  // Public API
  return {
    formatDateLabel,
    parseDate,
    formatISO,
    formatLocalDateTime,
    buildCalendar,
    navigate,
    getShiftDefaults,
    MONTH_NAMES,
    WEEK_DAYS
  };

})();

// Export for module systems (optional)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CalendarModule;
}

console.log('✅ CalendarModule loaded');
