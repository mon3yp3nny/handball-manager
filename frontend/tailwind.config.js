/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Legacy `primary` palette — repointed to the TVF red ramp so any
        // bg-primary-600 / text-primary-700 / focus:ring-primary-500 usage
        // already in the codebase picks up the brand without per-file edits.
        primary: {
          50:  '#FCE9EA',
          100: '#FCE9EA',
          200: '#F6BFC3',
          300: '#EF9097',
          400: '#E25960',
          500: '#D62027',
          600: '#C71D24',
          700: '#A8181D',
          800: '#8B1318',
          900: '#6B0F13',
        },
        // TVF brand palette — Hamburg-inspired navy + signal red on warm
        // canvas. Hex values mirror frontend/src/styles/tvf-tokens.css
        // (which is also imported globally so plain CSS can use --tvf-*).
        tvf: {
          navy: '#0E2A47',
          'navy-deep': '#081A2D',
          'navy-soft': '#233E5C',
          red: '#D62027',
          'red-deep': '#A8181D',
          'red-soft': '#FCE9EA',
          canvas: '#F4F1EA',
          surface: '#FFFFFF',
          'surface-2': '#F7F5EF',
          line: '#E6E2D8',
          'line-strong': '#D6D1C3',
          ink: '#0E2A47',
          'ink-2': '#4A5872',
          'ink-3': '#8A93A6',
          'ink-on-navy': '#F6F2E7',
          win: '#1F8A5B',
          draw: '#C8961A',
          court: '#16734E',
          sand: '#E9C775',
        },
      },
      fontFamily: {
        display: ['Anton', '"Bebas Neue"', 'Impact', 'sans-serif'],
        sans: ['Manrope', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
        num: ['Anton', '"Bebas Neue"', 'Impact', 'sans-serif'],
      },
      borderRadius: {
        'tvf-xs': '6px',
        'tvf-sm': '10px',
        'tvf-md': '14px',
        'tvf-lg': '20px',
        'tvf-xl': '28px',
      },
      boxShadow: {
        'tvf-sm': '0 1px 2px rgba(14, 42, 71, 0.06), 0 1px 1px rgba(14, 42, 71, 0.04)',
        'tvf-md': '0 4px 14px rgba(14, 42, 71, 0.08), 0 2px 4px rgba(14, 42, 71, 0.04)',
        'tvf-lg': '0 16px 40px rgba(14, 42, 71, 0.14), 0 4px 8px rgba(14, 42, 71, 0.06)',
      },
    },
  },
  plugins: [],
}
