/**
 * LIMS Draft Manager
 *
 * LocalStorage-д шинжилгээний ноорог (draft) өгөгдлийг хадгалах/сэргээх/устгах
 * Олон analysis form template-д давтагдаж байсан код-ыг нэгтгэсэн.
 *
 * Хэрэглээ:
 *   const draftMgr = new LIMSDraftManager('Aad');
 *   draftMgr.save({123: {m1: 10.5, m2: 10.6}});
 *   const drafts = draftMgr.restore();
 *   draftMgr.purge([123, 456]); // Тодорхой sample-ийн draft устгах
 *
 * Author: Gantulga (semmganaa@gmail.com)
 * Date: 2025-11-30
 */

(function(window) {
  'use strict';

  /**
   * Draft Manager Class
   */
  class LIMSDraftManager {
    /**
     * Constructor
     *
     * @param {string} analysisCode - Шинжилгээний код (жишээ: 'Aad', 'Mad', 'Vad')
     * @param {string} prefix - LocalStorage key prefix (default: 'draft_inputs_')
     */
    constructor(analysisCode, prefix = 'draft_inputs_') {
      if (!analysisCode) {
        throw new Error('LIMSDraftManager: analysisCode is required');
      }

      this.analysisCode = analysisCode;
      this.prefix = prefix;
      this.key = `${prefix}${analysisCode}`;

      // Quota exceeded эвент handler
      this.quotaExceededHandler = null;
    }

    /**
     * Draft өгөгдлийг localStorage-д хадгалах
     *
     * @param {Object} data - Хадгалах өгөгдөл (жишээ: {123: {m1: 10.5}, 456: {m1: 11.2}})
     * @param {boolean} merge - Өмнөх өгөгдөлтэй merge хийх үү (default: true)
     * @returns {boolean} Амжилттай эсэх
     */
    save(data, merge = true) {
      try {
        let toSave = data;

        // Merge хийх бол өмнөх өгөгдлийг авах
        if (merge) {
          const existing = this.restore(false, true);
          toSave = { ...existing, ...data };
        }

        // Timestamp нэмэх (cleanup-д ашиглах)
        toSave._meta = {
          savedAt: Date.now(),
          analysisCode: this.analysisCode
        };

        const jsonData = JSON.stringify(toSave);

        // Size шалгалт (5MB max - localStorage limit ойролцоо)
        const sizeInBytes = new Blob([jsonData]).size;
        const sizeInMB = (sizeInBytes / (1024 * 1024)).toFixed(2);

        if (sizeInBytes > 4.5 * 1024 * 1024) { // 4.5MB warning
          console.warn(
            `LIMSDraftManager: Draft size is large (${sizeInMB}MB). ` +
            `Consider cleaning old drafts.`
          );
        }

        localStorage.setItem(this.key, jsonData);

        console.log(
          `✅ Draft saved: ${this.analysisCode} (${sizeInMB}MB, ${Object.keys(toSave).filter(k => k !== '_meta').length} samples)`
        );

        return true;

      } catch (error) {
        if (this._isQuotaError(error)) {
          console.error('❌ LocalStorage quota exceeded! Cannot save draft.');

          // Callback дуудах
          if (this.quotaExceededHandler) {
            this.quotaExceededHandler(error);
          } else {
            // Default: Анхааруулга харуулах
            alert(
              'Storage is full! Please clear old draft data.'
            );
          }
        } else {
          console.error('❌ Failed to save draft:', error);
        }

        return false;
      }
    }

    /**
     * Draft өгөгдлийг localStorage-с сэргээх
     *
     * @param {boolean} includeMeta - _meta өгөгдлийг буцаах эсэх (default: false)
     * @returns {Object} Сэргээсэн өгөгдөл ({} хоосон бол)
     */
    restore(includeMeta = false, silent = false) {
      try {
        const jsonData = localStorage.getItem(this.key);

        if (!jsonData) {
          if (!silent) console.log(`ℹ️ No draft found for ${this.analysisCode}`);
          return {};
        }

        const data = JSON.parse(jsonData);

        // _meta-г тусад нь авах (sample тоо тооцохдоо оруулахгүй)
        const meta = data._meta || null;
        const sampleCount = Object.keys(data).filter(k => k !== '_meta').length;

        if (!silent) console.log(
          `✅ Draft restored: ${this.analysisCode} (${sampleCount} samples)`
        );

        // includeMeta=false бол _meta-г ХАСАЖ буцаах (ӨГӨГДЛИЙГ ӨӨРЧЛӨХГҮЙ)
        if (!includeMeta) {
          const { _meta, ...rest } = data;
          return rest;
        }

        return data;

      } catch (error) {
        console.error('❌ Failed to restore draft:', error);

        // Corrupt data байвал устгах
        this.purge();

        return {};
      }
    }

    /**
     * Draft-ийн metadata (savedAt timestamp) авах
     *
     * @returns {Object|null} Meta өгөгдөл эсвэл null
     */
    getMeta() {
      try {
        const jsonData = localStorage.getItem(this.key);
        if (!jsonData) return null;

        const data = JSON.parse(jsonData);
        return data._meta || null;
      } catch (error) {
        return null;
      }
    }

    /**
     * Draft өгөгдлийг бүхэлд нь эсвэл тодорхой sample-уудын хувьд устгах
     *
     * @param {Array<number>} sampleIds - Устгах sample IDs (optional)
     *        - Хоосон бол бүх draft устгана
     *        - Өгсөн бол зөвхөн тэдгээр sample-ийн draft устгана
     * @returns {boolean} Амжилттай эсэх
     */
    purge(sampleIds = []) {
      try {
        if (!sampleIds || sampleIds.length === 0) {
          // Бүх draft устгах
          localStorage.removeItem(this.key);
          console.log(`🗑️ All drafts purged: ${this.analysisCode}`);
          return true;
        }

        // Тодорхой sample-уудын draft устгах
        const existing = this.restore(false, true);
        let purgedCount = 0;

        sampleIds.forEach(id => {
          const key = String(id);
          if (existing[key]) {
            delete existing[key];
            purgedCount++;
          }
        });

        if (purgedCount > 0) {
          // Үлдсэн өгөгдлийг хадгалах (save() ашиглан _meta-г хадгална)
          if (Object.keys(existing).length === 0) {
            localStorage.removeItem(this.key);
          } else {
            this.save(existing, false); // merge=false, шинээр хадгалах
          }

          console.log(
            `🗑️ Drafts purged: ${this.analysisCode} (${purgedCount} samples)`
          );
        } else {
          console.log(`ℹ️ No matching drafts to purge: ${this.analysisCode}`);
        }

        return true;

      } catch (error) {
        console.error('❌ Failed to purge drafts:', error);
        return false;
      }
    }

    /**
     * Тодорхой sample-ийн draft өгөгдөл байгаа эсэхийг шалгах
     *
     * @param {number} sampleId - Sample ID
     * @returns {boolean} Draft байгаа эсэх
     */
    hasDraft(sampleId) {
      const drafts = this.restore(false, true);
      return !!drafts[String(sampleId)];
    }

    /**
     * Тодорхой sample-ийн draft өгөгдлийг авах
     *
     * @param {number} sampleId - Sample ID
     * @returns {Object|null} Draft data эсвэл null
     */
    getDraft(sampleId) {
      const drafts = this.restore(false, true);
      return drafts[String(sampleId)] || null;
    }

    /**
     * Тодорхой sample-ийн draft өгөгдлийг шинэчлэх
     *
     * @param {number} sampleId - Sample ID
     * @param {Object} data - Шинэчлэх өгөгдөл
     * @returns {boolean} Амжилттай эсэх
     */
    updateDraft(sampleId, data) {
      const drafts = this.restore(false, true);
      drafts[String(sampleId)] = data;
      return this.save(drafts, false);
    }

    /**
     * Draft өгөгдлийн хэмжээг авах (sample тоо)
     *
     * @returns {number} Draft-тай sample-ийн тоо
     */
    getCount() {
      const drafts = this.restore(false, true);
      return Object.keys(drafts).length;
    }

    /**
     * Бүх draft sample ID-уудыг авах
     *
     * @returns {Array<string>} Sample IDs
     */
    getSampleIds() {
      const drafts = this.restore(false, true);
      return Object.keys(drafts);
    }

    /**
     * Quota exceeded error handler тохируулах
     *
     * @param {Function} handler - Error handler function
     */
    setQuotaExceededHandler(handler) {
      this.quotaExceededHandler = handler;
    }

    /**
     * QuotaExceededError шалгах (cross-browser compatible)
     * Safari: code 22, Firefox: code 1014
     *
     * @param {Error} error - Шалгах error объект
     * @returns {boolean} QuotaExceededError эсэх
     */
    _isQuotaError(error) {
      return error?.name === 'QuotaExceededError' || error?.code === 22 || error?.code === 1014;
    }

    /**
     * Draft өгөгдлийг debug хэвлэх
     */
    debug() {
      const drafts = this.restore();
      console.group(`📋 Draft Debug: ${this.analysisCode}`);
      console.log('Key:', this.key);
      console.log('Sample count:', Object.keys(drafts).length);
      console.log('Data:', drafts);

      try {
        const jsonData = JSON.stringify(drafts);
        const sizeInBytes = new Blob([jsonData]).size;
        const sizeInKB = (sizeInBytes / 1024).toFixed(2);
        console.log('Size:', sizeInKB, 'KB');
      } catch (error) {
        console.error('Failed to calculate size:', error);
      }

      console.groupEnd();
    }
  }

  // Export to global scope
  window.LIMSDraftManager = LIMSDraftManager;

  // Хуучин draft-уудыг цэвэрлэх utility function
  /**
   * Бүх analysis-ийн draft-уудыг цэвэрлэх
   *
   * @param {number} maxAgeDays - Хамгийн их нас (өдрөөр)
   * @param {boolean} dryRun - Жинхэнээр устгахгүйгээр харах (default: false)
   * @returns {Object} Устгагдсан болон хадгалсан key-ууд
   */
  window.LIMS_DRAFT_CLEANUP = function(maxAgeDays = 30, dryRun = false) {
    const MS_PER_DAY = 24 * 60 * 60 * 1000;
    const maxAgeMs = maxAgeDays * MS_PER_DAY;
    const now = Date.now();
    const removed = [];
    const kept = [];

    console.group('🧹 LIMS Draft Cleanup');
    console.log('Max age:', maxAgeDays, 'days');
    console.log('Dry run:', dryRun);

    // localStorage.length нь loop дотор өөрчлөгдөж болно тул key-үүдийг эхлээд авах
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('draft_inputs_')) {
        keys.push(key);
      }
    }

    keys.forEach(key => {
      try {
        const rawData = localStorage.getItem(key);
        if (!rawData) return;

        const data = JSON.parse(rawData);
        const sizeInBytes = new Blob([rawData]).size;
        const sizeInKB = (sizeInBytes / 1024).toFixed(2);

        // Timestamp шалгах (_meta.savedAt)
        const savedAt = data._meta?.savedAt;
        let ageInDays = null;
        let shouldRemove = false;

        if (savedAt) {
          const ageMs = now - savedAt;
          ageInDays = Math.floor(ageMs / MS_PER_DAY);

          if (ageMs > maxAgeMs) {
            shouldRemove = true;
            console.log(`🗓️ Old draft: ${key} (${ageInDays} days old, ${sizeInKB}KB)`);
          }
        } else {
          // Хуучин format (timestamp байхгүй) - анхааруулах
          console.warn(`⚠️ Draft without timestamp: ${key} (${sizeInKB}KB) - will be updated on next save`);
        }

        // 100KB-аас ихийг анхааруулах
        if (sizeInBytes > 100 * 1024) {
          console.warn(`📦 Large draft: ${key} (${sizeInKB}KB)`);
        }

        if (shouldRemove) {
          if (!dryRun) {
            localStorage.removeItem(key);
            removed.push({ key, ageInDays, sizeInKB });
            console.log(`✅ Removed: ${key}`);
          } else {
            console.log(`[DRY RUN] Would remove: ${key}`);
          }
        } else {
          kept.push({ key, ageInDays, sizeInKB });
        }

      } catch (error) {
        console.error(`❌ Corrupt draft: ${key}`, error);

        if (!dryRun) {
          localStorage.removeItem(key);
          removed.push({ key, error: 'corrupt' });
          console.log(`✅ Removed corrupt draft: ${key}`);
        }
      }
    });

    console.log('---');
    console.log('Removed:', removed.length);
    console.log('Kept:', kept.length);
    console.groupEnd();

    return { removed, kept };
  };

  console.log('✅ LIMS Draft Manager loaded');

})(window);
