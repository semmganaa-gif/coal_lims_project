import { defineConfig } from 'vitest/config'
import { resolve } from 'path'

export default defineConfig({
  test: {
    // Test environment
    environment: 'jsdom',

    // Global variables
    globals: true,

    // Include patterns
    include: ['src/**/*.{test,spec}.{js,ts}'],

    // Coverage тохиргоо
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      reportsDirectory: './coverage-js',
      include: ['src/**/*.{js,ts}'],
      exclude: ['src/**/*.{test,spec}.{js,ts}', 'src/types.ts'],
    },
  },

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
})
