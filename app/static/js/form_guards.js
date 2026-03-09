/**
 * form_guards.js — beforeunload + double-submit protection
 *
 * Usage:
 *   // Mark form as dirty (unsaved changes)
 *   FormGuards.markDirty();
 *
 *   // Mark form as clean (after successful save)
 *   FormGuards.markClean();
 *
 *   // Wrap a save button to prevent double-submit
 *   FormGuards.guardButton(btnElement, asyncSaveFn);
 *
 *   // Or guard a button by ID
 *   FormGuards.guardById('btnSave', asyncSaveFn);
 */
(function(w) {
  'use strict';

  var _dirty = false;

  function onBeforeUnload(e) {
    if (_dirty) {
      e.preventDefault();
      e.returnValue = '';
      return '';
    }
  }

  var FormGuards = {
    /** Mark the page as having unsaved changes */
    markDirty: function() {
      if (!_dirty) {
        _dirty = true;
        w.addEventListener('beforeunload', onBeforeUnload);
      }
    },

    /** Mark the page as clean (no unsaved changes) */
    markClean: function() {
      _dirty = false;
      w.removeEventListener('beforeunload', onBeforeUnload);
    },

    /** Check if page has unsaved changes */
    isDirty: function() {
      return _dirty;
    },

    /**
     * Guard a button against double-submit.
     * Disables button during asyncFn execution, re-enables after.
     *
     * @param {HTMLElement} btn - The button element
     * @param {Function} asyncFn - Async function to run on click
     */
    guardButton: function(btn, asyncFn) {
      if (!btn) return;
      btn.addEventListener('click', async function(e) {
        if (btn.disabled) return;
        btn.disabled = true;
        var origHtml = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';
        try {
          await asyncFn(e);
        } catch (err) {
          logger.error('Save error:', err);
        } finally {
          btn.disabled = false;
          btn.innerHTML = origHtml;
        }
      });
    },

    /**
     * Guard button by element ID
     * @param {string} id - Button element ID
     * @param {Function} asyncFn - Async function to run on click
     */
    guardById: function(id, asyncFn) {
      var btn = document.getElementById(id);
      if (btn) this.guardButton(btn, asyncFn);
    }
  };

  w.FormGuards = FormGuards;
})(window);
