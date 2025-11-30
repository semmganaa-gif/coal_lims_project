// static/js/instrument_nav.js
(function () {
  const TABLES = [
    '#phosphorus-analysis-table',
    '#fluorine-analysis-table',
    '#chlorine-analysis-table'
  ];

  function isInAnyTable(el){
    return TABLES.some(sel => el.closest(sel));
  }

  document.addEventListener('keydown', (ev) => {
    const el = ev.target;
    if (!el.classList?.contains('form-input')) return;
    if (!isInAnyTable(el)) return;

    const keys = ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Enter'];
    if (!keys.includes(ev.key)) return;

    const row = el.closest('tr[data-sample-id]');
    const table = row.closest('table');
    const rows = Array.from(table.querySelectorAll('tbody tr[data-sample-id]'));
    const inputsRow = Array.from(row.querySelectorAll('.form-input'));
    const idx = inputsRow.indexOf(el);

    let target = null;
    if (ev.key === 'ArrowLeft')  target = inputsRow[(idx - 1 + inputsRow.length) % inputsRow.length];
    if (ev.key === 'ArrowRight' || ev.key === 'Enter') target = inputsRow[(idx + 1) % inputsRow.length];
    if (ev.key === 'ArrowUp' || ev.key === 'ArrowDown') {
      const dir = ev.key === 'ArrowDown' ? 1 : -1;
      const rIdx = rows.indexOf(row);
      const row2 = rows[rIdx + dir];
      if (row2) {
        const inputs2 = Array.from(row2.querySelectorAll('.form-input'));
        target = inputs2[Math.min(idx, inputs2.length - 1)];
      }
    }
    if (target){
      ev.preventDefault();            // Number input-ийн default ↑/↓ өсгөх үйлдлийг болиулна
      target.focus();
      target.select?.();
    }
  }, true); // capture=true => number input-ийн default-оос өмнө барина
})();
