/**
 * DataTables entry — jQuery + Bootstrap5 plugin, audit page-уудад.
 *
 * Ачаалах:
 *   {{ vite_js_tag('src/datatables.js') }}
 *
 * Бундл нь jQuery-г `window.$/jQuery` (main.js дотроос аль хэдийн глобал
 * болсон)-аар нийцэх дадлагатай.
 */

// jQuery нь main bundle-аас глобалаар бэлэн (window.jQuery)
// DataTables core + Bootstrap5 styling plugin
import 'datatables.net'
import 'datatables.net-bs5'

console.log('DataTables (jQuery + Bootstrap5) bundle loaded')
