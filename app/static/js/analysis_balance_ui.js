/* analysis_balance_ui.js — Balance serial connection UI
   (extracted from analysis_page.html)
   Requires: window.labBalance (serial_balance.js), window.EQ_I18N */

(function() {
  'use strict';

  var T = window.EQ_I18N || {};
  var $btnConnect = document.getElementById('btnConnectBalance');
  var $balanceStatus = document.getElementById('balanceStatus');
  var WEIGHT_COLUMNS = ['m1', 'm2', 'm3', 'weight', 'mass'];

  if (!$btnConnect || !$balanceStatus) {
    console.log('Balance UI not found on this page');
    return;
  }

  function updateBalanceStatus(message, type) {
    if (!type) type = 'secondary';
    $balanceStatus.textContent = message;
    $balanceStatus.className = 'badge bg-' + type + ' small';
  }

  $btnConnect.addEventListener('click', async () => {
    if (!window.labBalance) {
      alert(T.balanceNotLoaded || 'Balance module not loaded.');
      return;
    }

    if (!window.labBalance.isSupported()) {
      alert(T.webSerialNotSupported || 'Web Serial API is not supported. Please use Chrome 89+.');
      return;
    }

    if (window.labBalance.isConnected) {
      await window.labBalance.disconnect();
      $btnConnect.innerHTML = '<i class="bi bi-usb-plug"></i> ' + (T.connectBalance || 'Connect Balance');
      $btnConnect.classList.remove('btn-success');
      $btnConnect.classList.add('btn-outline-primary');
      updateBalanceStatus(T.notConnected || 'Not Connected', 'secondary');
      return;
    }

    updateBalanceStatus(T.connecting || 'Connecting...', 'warning');
    var connected = await window.labBalance.connect();

    if (connected) {
      $btnConnect.innerHTML = '<i class="bi bi-usb-plug-fill"></i> ' + (T.connected || 'Connected');
      $btnConnect.classList.remove('btn-outline-primary');
      $btnConnect.classList.add('btn-success');
      updateBalanceStatus(T.connected || 'Connected', 'success');
    } else {
      updateBalanceStatus(T.error || 'Error', 'danger');
    }
  });

  if (window.labBalance) {
    window.labBalance.onDisconnect = () => {
      $btnConnect.innerHTML = '<i class="bi bi-usb-plug"></i> ' + (T.connectBalance || 'Connect Balance');
      $btnConnect.classList.remove('btn-success');
      $btnConnect.classList.add('btn-outline-primary');
      updateBalanceStatus(T.disconnected || 'Disconnected', 'secondary');
    };
  }

  // F2 to fetch weight
  document.addEventListener('keydown', async (e) => {
    if (e.key !== 'F2') return;
    if (!window.labBalance || !window.labBalance.isConnected) return;

    var gridApis = [
      window.madGridApi, window.ashGridApi, window.vadGridApi,
      window.cvGridApi, window.mtGridApi, window.tsGridApi,
      window.trdGridApi, window.csnGridApi, window.giGridApi,
      window.cricSrGridApi, window.phosphorusGridApi,
      window.chlorineGridApi, window.fluorineGridApi,
      window.xyGridApi, window.solidGridApi, window.fmGridApi,
      window.sulfurGridApi
    ].filter(api => api != null);

    for (var i = 0; i < gridApis.length; i++) {
      var gridApi = gridApis[i];
      var focusedCell = gridApi.getFocusedCell?.();
      if (!focusedCell) continue;

      var colId = focusedCell.column.getColId();
      if (!WEIGHT_COLUMNS.includes(colId)) continue;

      e.preventDefault();
      e.stopPropagation();

      updateBalanceStatus(T.fetchingWeight || 'Fetching weight...', 'warning');
      var weight = await window.labBalance.getStableWeight();

      if (weight !== null) {
        var rowNode = gridApi.getDisplayedRowAtIndex(focusedCell.rowIndex);
        if (rowNode) {
          rowNode.setDataValue(colId, weight);
          gridApi.refreshCells({ rowNodes: [rowNode], columns: [colId] });
          updateBalanceStatus(weight.toFixed(4) + ' g', 'success');

          var currentIdx = WEIGHT_COLUMNS.indexOf(colId);
          if (currentIdx >= 0 && currentIdx < WEIGHT_COLUMNS.length - 1) {
            var nextCol = WEIGHT_COLUMNS[currentIdx + 1];
            setTimeout(() => {
              gridApi.setFocusedCell(focusedCell.rowIndex, nextCol);
              gridApi.startEditingCell({ rowIndex: focusedCell.rowIndex, colKey: nextCol });
            }, 50);
          }
        }
      } else {
        updateBalanceStatus(T.failedGetWeight || 'Failed to get weight', 'danger');
      }
      break;
    }
  });

  console.log('Balance integration loaded. Press F2 on m1/m2/m3 to fetch weight.');
})();
