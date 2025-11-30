// app/static/js/repeatability.js
// T (repeatability) limits per analysis code, central map
(function(w){
  'use strict';

  // ✅ ТӨВЛӨРСӨН: Серверээс бүх repeatability дүрмийг авна
  // Hardcoded fallback УСТГАСАН - бүгд app/config/repeatability.py-аас удирдагдана
  w.LIMS_LIMITS = w.LIMS_LIMIT_RULES || {};

  // Simple helper: returns numeric limit for code, optionally using avg to pick band.
  w.getRepeatabilityLimit = function(code, avg){
    const rule = (w.LIMS_LIMITS || {})[code];
    if(!rule) return null;
    if(rule.single) return rule.single.limit;
    const bands = rule.bands_detailed || rule.bands || [];
    if(bands.length === 0) return null;
    if(typeof avg === 'number'){
      for(const b of bands){
        if(avg <= b.upper) return b.limit;
      }
      return bands[bands.length-1].limit;
    }
    return bands[0].limit;
  };
})(window);
