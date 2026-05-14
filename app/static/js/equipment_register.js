/* app/static/js/equipment_register.js
 * Shared utilities for equipment register pages (Tabulator-based).
 * Eliminates duplicated selection/delete/count logic across 6 register templates.
 */

/**
 * Initialize standard register table behaviors: row selection, delete, total count.
 *
 * @param {Tabulator} table       - The Tabulator instance
 * @param {string}    confirmMsg  - i18n string for delete confirmation (e.g. "rows will be deleted. Continue?")
 */
function initRegisterTable(table, confirmMsg) {
  var editBtn = document.getElementById('btn-edit-row');
  var deleteBtn = document.getElementById('btn-delete-row');
  var countBadge = document.getElementById('selected-count-badge');

  // Selection change handler
  table.on('rowSelectionChanged', function(data) {
    if (editBtn)   editBtn.disabled = (data.length !== 1);
    if (deleteBtn) deleteBtn.disabled = (!data.length);
    if (countBadge) {
      if (data.length) {
        countBadge.textContent = data.length;
        countBadge.classList.remove('d-none');
      } else {
        countBadge.classList.add('d-none');
      }
    }
  });

  // Total count
  var totalEl = document.getElementById('eqTotalCount');
  if (totalEl) totalEl.textContent = table.getData().length;

  // Delete handler
  window.deleteSelectedRows = function() {
    var sel = table.getSelectedData();
    if (!sel.length || !confirm(sel.length + ' ' + confirmMsg)) return;
    var form = document.getElementById('deleteForm');
    form.querySelectorAll('input[name="item_ids"]').forEach(function(el) { el.remove(); });
    sel.forEach(function(row) {
      if (row.id) {
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'item_ids';
        input.value = row.id;
        form.appendChild(input);
      }
    });
    form.submit();
  };

  // CSP-compatible click handlers (inline onclick-ийг орлоно).
  // editSelectedRow нь template бүрт өөрөөр тодорхойлогдох тул click үед
  // шалгаж дуудна.
  if (editBtn) {
    editBtn.addEventListener('click', function() {
      if (typeof window.editSelectedRow === 'function') window.editSelectedRow();
    });
  }
  if (deleteBtn) {
    deleteBtn.addEventListener('click', window.deleteSelectedRows);
  }
}
