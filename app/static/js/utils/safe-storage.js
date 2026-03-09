/**
 * Safe Storage Utility
 *
 * localStorage/sessionStorage алдааг аюулгүй барьдаг.
 * - QuotaExceededError (storage дүүрсэн)
 * - SecurityError (private browsing)
 * - Бусад storage алдаанууд
 */
const SafeStorage = {
    /**
     * Storage-д утга хадгалах
     * @param {string} key - Түлхүүр
     * @param {*} value - Утга
     * @param {boolean} useSession - sessionStorage ашиглах эсэх (default: false)
     */
    set(key, value, useSession = false) {
        const val = String(value ?? '');
        let localOk = false;
        try {
            localStorage.setItem(key, val);
            localOk = true;
        } catch (e) {
            // localStorage бүтэлгүйтвэл sessionStorage руу fallback
            if (e.name === 'QuotaExceededError') {
                logger.warn('SafeStorage: localStorage quota exceeded, falling back to sessionStorage');
            }
        }
        try {
            if (useSession || !localOk) {
                sessionStorage.setItem(key, val);
            }
        } catch (e) {
            // sessionStorage бас бүтэлгүйтвэл алгасах (private browsing гэх мэт)
        }
    },

    /**
     * Storage-аас утга унших
     * @param {string} key - Түлхүүр
     * @param {string} defaultVal - Default утга
     * @returns {string}
     */
    get(key, defaultVal = '') {
        try {
            const v = localStorage.getItem(key);
            if (v !== null) return v;
        } catch (e) {
            // localStorage унших боломжгүй
        }
        try {
            const v2 = sessionStorage.getItem(key);
            return v2 ?? defaultVal;
        } catch (e) {
            // sessionStorage унших боломжгүй
        }
        return defaultVal;
    },

    /**
     * Storage-аас утга устгах
     * @param {string} key - Түлхүүр
     */
    del(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            // localStorage устгах боломжгүй
        }
        try {
            sessionStorage.removeItem(key);
        } catch (e) {
            // sessionStorage устгах боломжгүй
        }
    },

    /**
     * Session storage-д хадгалах (түр)
     * @param {string} key - Түлхүүр
     * @param {*} value - Утга
     */
    setSession(key, value) {
        try {
            sessionStorage.setItem(key, String(value ?? ''));
        } catch (e) {
            // Алгасах - private browsing гэх мэт
        }
    },

    /**
     * Session storage-аас унших
     * @param {string} key - Түлхүүр
     * @param {string} defaultVal - Default утга
     * @returns {string}
     */
    getSession(key, defaultVal = '') {
        try {
            return sessionStorage.getItem(key) ?? defaultVal;
        } catch (e) {
            return defaultVal;
        }
    },

    /**
     * Session storage-аас устгах
     * @param {string} key - Түлхүүр
     */
    delSession(key) {
        try {
            sessionStorage.removeItem(key);
        } catch (e) {
            // Алгасах
        }
    }
};

// Global-д export
window.SafeStorage = SafeStorage;
