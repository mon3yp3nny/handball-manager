/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eef5ff',
          100: '#d9e8ff',
          200: '#bcd7ff',
          300: '#8cbfff',
          400: '#589dff',
          500: '#3178f5',
          600: '#1b5ee0',
          700: '#144ab6',
          800: '#153e96',
          900: '#17377a',
        },
      },
    },
  },
  plugins: [],
}
