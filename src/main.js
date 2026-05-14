/**
 * LIMS Main Entry Point — Vite bundle
 *
 * Бүх vendor library (Bootstrap, jQuery, Alpine, htmx, etc.) болон LIMS-ийн
 * глобал helper-уудыг агуулна. Production-д `npm run build` гүйцэтгэхэд
 * `app/static/dist/js/main-[hash].js` болж хадгалагдана.
 *
 * Development: npm run dev      (Vite dev server, HMR)
 * Production:  npm run build    (vite build → manifest.json)
 */

// ─────────────────────────────────────────────────────────────
// Vendor libraries — CDN-ээс bundle руу шилжүүлсэн
// ─────────────────────────────────────────────────────────────

// jQuery — DataTables-д шаардлагатай
import $ from 'jquery'
window.$ = window.jQuery = $

// Bootstrap (Popper-тэй bundle)
import * as bootstrap from 'bootstrap'
window.bootstrap = bootstrap

// Alpine.js + collapse plugin
import Alpine from 'alpinejs'
import collapse from '@alpinejs/collapse'
Alpine.plugin(collapse)
window.Alpine = Alpine
// Note: Alpine.start() нь DOMContentLoaded-д автомат дуудагдана

// htmx
import 'htmx.org'
// Note: htmx нь global `htmx` объект өөрөө үүсгэнэ

// ─────────────────────────────────────────────────────────────
// LIMS глобал namespace + helpers
// ─────────────────────────────────────────────────────────────

window.LIMS = window.LIMS || {}

/**
 * Ээлжийн огноо авах
 * Шөнийн ээлж (0:00-6:59) бол өмнөх өдрийн огноо буцаана
 */
window.LIMS.getShiftDate = function () {
  const d = new Date()
  const h = d.getHours()
  if (h < 7) {
    d.setDate(d.getDate() - 1)
  }
  return (
    d.getFullYear() +
    '-' +
    String(d.getMonth() + 1).padStart(2, '0') +
    '-' +
    String(d.getDate()).padStart(2, '0')
  )
}
window.getShiftDate = window.LIMS.getShiftDate

/**
 * Огнооны input-үүдэд өнөөдрийн огноог default болгох
 */
document.addEventListener('DOMContentLoaded', function () {
  const today = new Date().toISOString().split('T')[0]
  document.querySelectorAll('input[type="date"]').forEach(function (input) {
    if (!input.value && !input.dataset.noDefault) {
      input.value = today
    }
  })
})

/**
 * CSRF token helper — htmx болон fetch-д ашиглах
 */
window.LIMS.getCsrfToken = function () {
  return document.querySelector('meta[name="csrf-token"]')?.content || ''
}

/**
 * Toast notification helper (Bootstrap toast)
 */
window.LIMS.toast = function (message, type = 'info') {
  const toastContainer =
    document.getElementById('toast-container') || createToastContainer()

  const toastEl = document.createElement('div')
  toastEl.className = `toast align-items-center text-white bg-${type} border-0`
  toastEl.setAttribute('role', 'alert')
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `

  toastContainer.appendChild(toastEl)
  const toast = new bootstrap.Toast(toastEl, { delay: 3000 })
  toast.show()
  toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove())
}

function createToastContainer() {
  const container = document.createElement('div')
  container.id = 'toast-container'
  container.className = 'toast-container position-fixed top-0 end-0 p-3'
  container.style.zIndex = '1100'
  document.body.appendChild(container)
  return container
}

// Export for ES modules
export { }

console.log('LIMS main.js bundle loaded (Bootstrap, jQuery, Alpine, htmx)')
