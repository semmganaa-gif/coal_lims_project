/**
 * Chart.js entry — conditional bundle (dashboard/chart page-уудад).
 *
 * Chart.js v4.4.1 (~200KB) тул main bundle-аас ялгасан. Ачаалах:
 *   {{ vite_js_tag('src/chart.js') }}
 *
 * Auto-register бүх controller, scale, plugin (default behavior).
 */

import {
  Chart,
  registerables,
} from 'chart.js'

Chart.register(...registerables)

// Global API
window.Chart = Chart

console.log('Chart.js v4 bundle loaded')
