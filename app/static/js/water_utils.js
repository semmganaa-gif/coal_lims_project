/**
 * water_utils.js — Усны лабын дундын utility functions
 * water_summary.js, water_archive.js хоёулаа ашиглана
 */
(function(w) {
  'use strict';

  /* ======== UTILITY FUNCTIONS ======== */

  function safeNumber(val) {
    if (val === null || val === undefined || val === '' || val === 'null') return null;
    var str = String(val).replace(',', '').trim();
    var num = parseFloat(str);
    return isNaN(num) ? null : num;
  }

  function formatValue(code, val) {
    if (val == null || val === '') return '';
    var n = parseFloat(val);
    if (isNaN(n)) return String(val);
    if (Math.abs(n) < 0.01 && n !== 0) return n.toExponential(2);
    if (n === Math.floor(n)) return n.toString();
    return n.toFixed(n < 1 ? 3 : 2);
  }

  function formatLimit(limit) {
    if (!limit) return '';
    if (Array.isArray(limit)) {
      var lo = limit[0], hi = limit[1];
      if (lo !== null && hi !== null) return lo + '\u2014' + hi;
      if (hi !== null) return '\u2264' + hi;
      if (lo !== null) return '\u2265' + lo;
    }
    return String(limit);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* ======== LIMIT CHECK FUNCTIONS ======== */

  function isOverLimit(limit, value) {
    if (!limit || value == null) return false;
    var n = parseFloat(value);
    if (isNaN(n)) return false;
    if (Array.isArray(limit)) {
      var lo = limit[0], hi = limit[1];
      return (lo !== null && n < lo) || (hi !== null && n > hi);
    }
    return false;
  }

  function isWithinLimit(limit, value) {
    if (!limit || value == null) return false;
    var n = parseFloat(value);
    if (isNaN(n)) return false;
    if (Array.isArray(limit)) {
      var lo = limit[0], hi = limit[1];
      return !((lo !== null && n < lo) || (hi !== null && n > hi));
    }
    return false;
  }

  function isDetectFail(value) {
    if (value == null || value === '') return false;
    var s = String(value).trim().toLowerCase();
    if (['илрэсэн', 'илэрсэн', 'detected', '+'].indexOf(s) !== -1) return true;
    var n = parseFloat(value);
    return !isNaN(n) && n > 0;
  }

  function isDetectPass(value) {
    if (value == null || value === '') return false;
    var s = String(value).trim().toLowerCase();
    if (['илрээгүй', 'not detected', '-', '0'].indexOf(s) !== -1) return true;
    var n = parseFloat(value);
    return !isNaN(n) && n === 0;
  }

  /* ======== COLUMN DEFINITIONS ======== */

  // Усны химийн баганууд — mns_limit серверээс ирнэ (mergeMnsLimits)
  // primary: true = үргэлж харагдана
  var WATER_CHEM_COLUMNS = [
    { code: 'COLOR', name: 'Color', shortName: 'Color', unit: '°', mns_limit: null, primary: true },
    { code: 'EC', name: 'Electrical Conductivity', shortName: 'EC', unit: 'µS/cm', mns_limit: null, primary: true },
    { code: 'PH', name: 'pH', shortName: 'pH', unit: '', mns_limit: null, primary: true },
    { code: 'F_W', name: 'Fluoride', shortName: 'F⁻', unit: 'mg/L', mns_limit: null, primary: true },
    { code: 'CL_FREE', name: 'Free Chlorine', shortName: 'Cl₂', unit: 'mg/L', mns_limit: null, primary: true },
    { code: 'HARD', name: 'Total Hardness', shortName: 'Hard', unit: 'meq/L', mns_limit: null },
    { code: 'NH4', name: 'Ammonium Ion', shortName: 'NH₄⁺', unit: 'mg/L', mns_limit: null },
    { code: 'NO2', name: 'Nitrite Ion', shortName: 'NO₂⁻', unit: 'mg/L', mns_limit: null },
    { code: 'FE_W', name: 'Iron', shortName: 'Fe', unit: 'mg/L', mns_limit: null },
    { code: 'TDS', name: 'Total Dissolved Solids', shortName: 'TDS', unit: 'mg/L', mns_limit: null },
    { code: 'CL_W', name: 'Chloride', shortName: 'Cl⁻', unit: 'mg/L', mns_limit: null },
    { code: 'PO4', name: 'Phosphate Ion', shortName: 'PO₄³⁻', unit: 'mg/L', mns_limit: null },
    { code: 'BOD', name: 'Biochemical Oxygen Demand', shortName: 'BOD', unit: 'mg/L', mns_limit: null },
    { code: 'SLUDGE_VOL', name: 'Sludge Volume', shortName: 'SV', unit: 'mL', mns_limit: null },
    { code: 'SLUDGE_DOSE', name: 'Sludge Dose', shortName: 'SD', unit: 'g/L', mns_limit: null },
    { code: 'SLUDGE_INDEX', name: 'Sludge Index', shortName: 'SI', unit: 'mL/g', mns_limit: null }
  ];

  // Микробиологийн баганууд
  var MICRO_COLUMNS = [
    { code: 'cfu_22', headerName: 'CFU 22°C', headerTooltip: 'MNS ISO 6222:1998 / per 1 mL ≤100', mns_limit: [null, 100], integer: true },
    { code: 'cfu_37', headerName: 'CFU 37°C', headerTooltip: 'MNS ISO 6222:1998 / per 1 mL ≤100', mns_limit: [null, 100], integer: true },
    { code: 'cfu_avg', headerName: 'CFU Avg', headerTooltip: 'Water: MNS ISO 6222 ≤100 / Swab: MNS 6410 <100', mns_limit: [null, 100], integer: true },
    { code: 'ecoli', headerName: 'E.coli', headerTooltip: 'Water: MNS ISO 9308-1 / Swab: MNS 6410:2018', detect: true, italic: true },
    { code: 'salmonella', headerName: 'Salmonella', headerTooltip: 'Water: MNS ISO 19250 / Swab: MNS 6410:2018', detect: true, italic: true },
    { code: 'staph', headerName: 'S.aureus', headerTooltip: 'Air: MNS 5484 / Swab: MNS 6410:2018', detect: true, italic: true },
    { code: 'air_cfu', headerName: 'Bacteria Count', headerTooltip: 'MNS 5484:2005 / per 1m³ <3000', mns_limit: [null, 3000], integer: true }
  ];

  /**
   * Серверээс ирсэн chem_params дахь mns_limit-ийг WATER_CHEM_COLUMNS руу merge хийх.
   * @param {Array} serverParams - [{code, name, unit, mns_limit}, ...]
   */
  function mergeMnsLimits(serverParams) {
    if (!serverParams || !serverParams.length) return;
    var limitMap = {};
    for (var i = 0; i < serverParams.length; i++) {
      var p = serverParams[i];
      if (p.mns_limit) {
        // Python tuple → JS array: (None, 15) → [null, 15]
        limitMap[p.code] = Array.isArray(p.mns_limit) ? p.mns_limit : [null, p.mns_limit];
      }
    }
    for (var j = 0; j < WATER_CHEM_COLUMNS.length; j++) {
      var col = WATER_CHEM_COLUMNS[j];
      if (limitMap[col.code]) {
        col.mns_limit = limitMap[col.code];
      }
    }
  }

  /* ======== PUBLIC API ======== */

  w.WATER_UTILS = {
    safeNumber: safeNumber,
    formatValue: formatValue,
    formatLimit: formatLimit,
    escapeHtml: escapeHtml,
    isOverLimit: isOverLimit,
    isWithinLimit: isWithinLimit,
    isDetectFail: isDetectFail,
    isDetectPass: isDetectPass,
    WATER_CHEM_COLUMNS: WATER_CHEM_COLUMNS,
    MICRO_COLUMNS: MICRO_COLUMNS,
    mergeMnsLimits: mergeMnsLimits
  };

})(window);
