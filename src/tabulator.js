/**
 * Tabulator entry — chemical list + equipment journal-уудад.
 *
 * Ачаалах:
 *   {{ vite_js_tag('src/tabulator.js') }}
 *
 * `window.Tabulator` глобал — legacy code-той нийцнэ.
 */

import { TabulatorFull as Tabulator } from 'tabulator-tables'

window.Tabulator = Tabulator

console.log('Tabulator-tables v5 bundle loaded')
