/** @type {import('tailwindcss').Config} */
export default {
  // Bootstrap-тэй conflict үүсэхгүйн тулд prefix ашиглах
  prefix: 'tw-',

  content: [
    './app/templates/**/*.html',
    './src/**/*.{js,ts}',
  ],

  theme: {
    extend: {
      // ER Lab branding colors (custom.css :root-ээс)
      colors: {
        'er-blue': '#3a8bc7',
        'er-yellow': '#f7d002',
        'er-tan': '#b99c75',
        'er-black': '#333132',
        'er-orange': '#f0892f',
        'lims': {
          bg: '#f5f7fa',
          surface: '#ffffff',
          border: 'rgba(0, 0, 0, 0.1)',
        }
      },

      // Custom breakpoints
      screens: {
        'xs': '475px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
      },

      // Z-index (Bootstrap-тэй зохицох)
      zIndex: {
        'drawer': '1040',
        'drawer-backdrop': '1035',
        'sticky': '1020',
        'navbar': '1030',
      },

      // Drawer animation
      animation: {
        'slide-in-left': 'slideInLeft 0.3s ease-out',
        'slide-out-left': 'slideOutLeft 0.3s ease-in',
        'fade-in': 'fadeIn 0.2s ease-out',
      },

      keyframes: {
        slideInLeft: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        slideOutLeft: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-100%)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },

      // Typography
      fontFamily: {
        'sans': ['Noto Sans', 'sans-serif'],
      },

      // Shadows
      boxShadow: {
        'lims': '0 2px 8px rgba(0, 0, 0, 0.1)',
        'lims-lg': '0 4px 16px rgba(0, 0, 0, 0.12)',
        'drawer': '4px 0 16px rgba(0, 0, 0, 0.15)',
      },
    },
  },

  plugins: [
    require('@tailwindcss/forms'),
  ],

  // Bootstrap classes-ийг purge хийхгүй
  safelist: [
    { pattern: /^(bg|text|border)-(primary|secondary|success|danger|warning|info)/ },
  ],
}
