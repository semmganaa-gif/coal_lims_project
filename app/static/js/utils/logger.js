/**
 * Production-safe logging utility
 *
 * Development режимд л console-руу log бичнэ.
 * Production-д юу ч хийхгүй (performance сайжруулах).
 *
 * Usage:
 *   logger.log('Information message');
 *   logger.warn('Warning message');
 *   logger.error('Error message');
 */

const logger = {
  /**
   * Development режим эсэхийг шалгах.
   * Flask debug режимтэй синхрончлохыг хичээх.
   */
  isDevelopment() {
    // Check if we're in development mode
    // You can set this via Flask template: <script>window.DEBUG = {{ 'true' if config.DEBUG else 'false' }};</script>
    return window.DEBUG === true || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  },

  /**
   * Мэдээллийн лог (console.log орлох)
   */
  log(...args) {
    if (this.isDevelopment()) {
      console.log(...args);
    }
  },

  /**
   * Сэрэмжлүүлэг (console.warn орлох)
   */
  warn(...args) {
    if (this.isDevelopment()) {
      console.warn(...args);
    }
  },

  /**
   * Алдаа (console.error орлох)
   * Production-д бас харуулна (алдаа гарсан тохиолдолд)
   */
  error(...args) {
    console.error(...args);
  },

  /**
   * Debug мэдээлэл (development-д л)
   */
  debug(...args) {
    if (this.isDevelopment()) {
      console.debug(...args);
    }
  }
};

// Export for modules or make globally available
if (typeof module !== 'undefined' && module.exports) {
  module.exports = logger;
} else {
  window.logger = logger;
}
