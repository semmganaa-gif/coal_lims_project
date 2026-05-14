/**
 * AG Grid entry — conditional bundle (use_aggrid=True үед ачаалагдана).
 *
 * AG Grid Community v32 (~2MB) тул main bundle-аас ялгасан. Зөвхөн analysis
 * form + Aggrid хүснэгтэй хуудсанд `{{ vite_js_tag('src/aggrid.js') }}`-аар
 * ачаална.
 */

// AG Grid v32 Community — namespace import (CDN-ийн `window.agGrid`-тэй ижил API)
import * as agGrid from 'ag-grid-community'

// Global API (legacy code зөрчилгүй ажиллах)
window.agGrid = agGrid

// CSS-ийг тус тусын CSS файлаар (хэшлэгдсэн URL-аар) хэрэглэгчийн templates
// css link-ээр ачаална — JS bundle-д CSS embed хийхгүй.

console.log('AG Grid v32 bundle loaded')
