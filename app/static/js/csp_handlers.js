/**
 * CSP-compatible event delegation framework.
 *
 * Inline `onclick=""`, `onchange=""`, `onsubmit=""` handlers-ыг template-ээс
 * хасаж энд төвлөрүүлсэн action dispatcher-аар ажиллуулна. Энэ нь CSP-ийн
 * `script-src 'self' 'nonce-X'` (no `unsafe-inline`) нөхцөлд кодыг ажиллуулах
 * стандарт арга юм.
 *
 * Хэрэглэх загвар:
 *
 *   <button data-action="save-results">Save</button>
 *   <input data-change-action="auto-submit-form">
 *   <form data-submit-action="confirm-submit" data-confirm="Итгэлтэй юу?">
 *
 * Action бүрчлэн `LIMS_ACTIONS`-д бүртгэнэ:
 *
 *   window.LIMS_ACTIONS['save-results'] = (el, e) => saveResults();
 *   window.LIMS_ACTIONS['quick-time']   = (el) => setQuickTime(el.dataset.time);
 *
 * Migration-ийн эхэн үед feature тус бүр өөрийн module-д action бүртгэнэ
 * (equipment_actions.js, water_actions.js, etc.).
 */

(function () {
  'use strict';

  // Public action registry — feature module-ууд энэ дотор бичилт хийнэ.
  window.LIMS_ACTIONS = window.LIMS_ACTIONS || {};

  // ------------------------------------------------------------------------
  // Built-in actions (frequently used, low-risk)
  // ------------------------------------------------------------------------
  Object.assign(window.LIMS_ACTIONS, {
    'reload': function (el, e) { e.preventDefault(); location.reload(); },
    'back': function (el, e) { e.preventDefault(); history.back(); },
    'print': function (el, e) { e.preventDefault(); window.print(); },
    'submit-form': function (el) {
      var form = el.form || el.closest('form');
      if (form) form.submit();
    },
    'click-target': function (el, e) {
      // <button data-action="click-target" data-target="#fileInput">
      var t = document.querySelector(el.dataset.target);
      if (t) t.click();
    },
    'hide-self': function (el) { el.style.display = 'none'; },
    'noop': function (el, e) { e.preventDefault(); },
    'stop-propagation': function (el, e) { e.stopPropagation(); },
    'prevent-default': function (el, e) { e.preventDefault(); },
    'uppercase': function (el) { el.value = (el.value || '').toUpperCase(); },
    'navigate': function (el, e) {
      e.preventDefault();
      var href = el.dataset.href;
      if (href) window.location = href;
    },
    'toggle-next-class': function (el) {
      var sib = el.nextElementSibling;
      if (sib && el.dataset.className) sib.classList.toggle(el.dataset.className);
    },
    'remove-closest': function (el) {
      var sel = el.dataset.selector;
      var target = sel ? el.closest(sel) : null;
      if (target) target.remove();
    },
    'hide-element': function (el) {
      var sel = el.dataset.target;
      var target = sel ? document.querySelector(sel) : null;
      if (target) target.style.display = 'none';
    },
    'toggle-target': function (el) {
      // jQuery $('#sel').toggle() equivalent
      var sel = el.dataset.target;
      var t = sel ? document.querySelector(sel) : null;
      if (!t) return;
      var hidden = window.getComputedStyle(t).display === 'none';
      t.style.display = hidden ? '' : 'none';
    },
    'toggle-class-in-parent': function (el) {
      // Toggle data-class-name on parent's element matching data-selector.
      // <div class="card">
      //   <div data-action="toggle-class-in-parent" data-selector=".body" data-class-name="d-none">Click</div>
      //   <div class="body">...</div>
      // </div>
      var sel = el.dataset.selector;
      var cls = el.dataset.className;
      if (!sel || !cls || !el.parentElement) return;
      var t = el.parentElement.querySelector(sel);
      if (t) t.classList.toggle(cls);
    },
  });

  // ------------------------------------------------------------------------
  // Positional arg reader — reads data-arg-0, data-arg-1, ... from element
  // ------------------------------------------------------------------------
  function readPositionalArgs(el) {
    var args = [];
    var i = 0;
    while (true) {
      var attr = 'data-arg-' + i;
      if (!el.hasAttribute(attr)) break;
      var raw = el.getAttribute(attr);
      args.push(coerceArg(raw, el));
      i++;
    }
    return args;
  }

  function coerceArg(raw, el) {
    if (raw === 'this') return el;
    if (raw === 'this.value') return el.value;
    if (raw === 'this.checked') return el.checked;
    if (raw === 'this.id') return el.id;
    if (raw === 'this.name') return el.name;
    if (raw === 'true') return true;
    if (raw === 'false') return false;
    if (raw === 'null') return null;
    if (/^-?\d+$/.test(raw)) return parseInt(raw, 10);
    if (/^-?\d+\.\d+$/.test(raw)) return parseFloat(raw);
    return raw;
  }

  // ------------------------------------------------------------------------
  // Dispatcher — supports per-event-type action OR generic data-action
  // ------------------------------------------------------------------------
  function dispatch(eventType) {
    return function (e) {
      var attrName = 'data-' + eventType + '-action';
      var el = e.target.closest('[' + attrName + ']');
      var action = el ? el.getAttribute(attrName) : null;

      if (!action) {
        el = e.target.closest('[data-action]');
        action = el ? el.getAttribute('data-action') : null;
      }
      if (!el || !action) return;

      var handler = window.LIMS_ACTIONS[action];
      if (handler) {
        handler(el, e);
        return;
      }
      // Fallback: if action looks like a function name and it's defined globally,
      // call it with positional args read from data-arg-0, data-arg-1, ...
      // `this` literal is converted to the event element.
      var fn = window[action];
      if (typeof fn === 'function') {
        var args = readPositionalArgs(el);
        fn.apply(null, args);
        return;
      }
      if (window.console && console.warn) {
        console.warn('No LIMS_ACTIONS handler for: ' + action);
      }
    };
  }

  document.addEventListener('click', dispatch('click'));
  document.addEventListener('change', dispatch('change'));
  document.addEventListener('input', dispatch('input'));
  document.addEventListener('submit', dispatch('submit'));

  // ------------------------------------------------------------------------
  // Convenience helpers (legacy from April 22 session)
  // ------------------------------------------------------------------------

  // [data-autosubmit] — input/select change → submit parent form
  document.addEventListener('change', function (e) {
    var el = e.target.closest('[data-autosubmit]');
    if (!el) return;
    var form = el.form || el.closest('form');
    if (form) form.submit();
  });

  // <form data-confirm="..."> — confirm() before submit
  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    var msg = form.dataset.confirm;
    if (msg && !window.confirm(msg)) {
      e.preventDefault();
    }
  });

  // <a data-click-confirm="..."> — confirm() before click; cancel if rejected
  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-click-confirm]');
    if (!el) return;
    var msg = el.dataset.clickConfirm;
    if (msg && !window.confirm(msg)) {
      e.preventDefault();
      e.stopImmediatePropagation();
    }
  }, true);  // capture phase — run before action handlers
})();
