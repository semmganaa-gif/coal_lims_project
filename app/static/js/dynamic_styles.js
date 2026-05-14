/* dynamic_styles.js — CSP-safe dynamic styling
 *
 * Server-rendered HTML can't have inline `style="..."` attributes (CSP блоклоно).
 * Сервер тэдгээрийг `data-*` attribute хэлбэрээр гаргаж энд DOM API-аар
 * style-ыг тогтооно. JS-ээс DOM API-аар тохируулсан style нь CSP-аас
 * чөлөөлөгдсөн (зөвхөн HTML attribute дээрх inline style блоклогдоно).
 *
 * Дэмжигдэх data-* атрибутууд:
 *   data-anim-delay="0.05"      → element.style.animationDelay = "0.05s"
 *   data-anim-delay-index="3"   → multiplied by data-anim-step (default 0.05)
 *   data-anim-step="0.06"       → step seconds for index-based delay
 *   data-bg-color="#abcdef"     → element.style.background = value
 *   data-bg-gradient="135deg, #c1, #c2"  → linear-gradient
 *   data-text-color="#abcdef"   → element.style.color = value
 *   data-border-color="#abcdef" → element.style.borderColor = value
 *   data-width-pct="50"         → element.style.width = "50%"
 *   data-progress="50"          → same as data-width-pct (semantic alias)
 */

(function () {
  'use strict';

  function applyDynamicStyles(root) {
    root = root || document;

    root.querySelectorAll('[data-anim-delay]').forEach(function (el) {
      el.style.animationDelay = el.dataset.animDelay + 's';
    });

    root.querySelectorAll('[data-anim-delay-index]').forEach(function (el) {
      var idx = parseInt(el.dataset.animDelayIndex, 10) || 0;
      var step = parseFloat(el.dataset.animStep) || 0.05;
      el.style.animationDelay = (idx * step) + 's';
    });

    root.querySelectorAll('[data-bg-color]').forEach(function (el) {
      el.style.background = el.dataset.bgColor;
    });

    root.querySelectorAll('[data-bg-gradient]').forEach(function (el) {
      el.style.background = 'linear-gradient(' + el.dataset.bgGradient + ')';
    });

    root.querySelectorAll('[data-text-color]').forEach(function (el) {
      el.style.color = el.dataset.textColor;
    });

    root.querySelectorAll('[data-border-color]').forEach(function (el) {
      el.style.borderColor = el.dataset.borderColor;
    });

    root.querySelectorAll('[data-width-pct], [data-progress]').forEach(function (el) {
      var pct = el.dataset.widthPct || el.dataset.progress;
      el.style.width = pct + '%';
    });

    // unit card: dynamic brand color → background gradient + CSS variable
    root.querySelectorAll('[data-unit-color]').forEach(function (el) {
      var c = el.dataset.unitColor;
      el.style.background = 'linear-gradient(135deg, ' + c + ', ' + c + 'cc)';
      el.style.setProperty('--card-shadow', c + '55');
    });

    // Generic CSS custom property setter: data-css-var-NAME="value"
    root.querySelectorAll('*').forEach(function (el) {
      for (var i = 0; i < el.attributes.length; i++) {
        var attr = el.attributes[i];
        if (attr.name.startsWith('data-css-var-')) {
          var varName = '--' + attr.name.slice('data-css-var-'.length);
          el.style.setProperty(varName, attr.value);
        }
      }
    });
  }

  // Initial paint after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      applyDynamicStyles(document);
    });
  } else {
    applyDynamicStyles(document);
  }

  // Expose for dynamically inserted content (htmx, AG Grid, etc.)
  window.applyDynamicStyles = applyDynamicStyles;

  // htmx integration — re-apply after every swap
  document.addEventListener('htmx:afterSwap', function (e) {
    applyDynamicStyles(e.detail.target);
  });

  // MutationObserver — automatically style elements added by 3rd-party widgets
  // (Tabulator, AG Grid row renderers, modals, dropdowns, async fetch).
  // Throttled with requestAnimationFrame to avoid layout thrashing.
  function startObserver() {
    var pending = new Set();
    var scheduled = false;
    function flush() {
      scheduled = false;
      pending.forEach(function (node) { applyDynamicStyles(node); });
      pending.clear();
    }
    var observer = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var m = mutations[i];
        for (var j = 0; j < m.addedNodes.length; j++) {
          var n = m.addedNodes[j];
          if (n.nodeType === 1) pending.add(n);  // ELEMENT_NODE
        }
      }
      if (pending.size && !scheduled) {
        scheduled = true;
        requestAnimationFrame(flush);
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.body) {
    startObserver();
  } else {
    document.addEventListener('DOMContentLoaded', startObserver);
  }
})();
