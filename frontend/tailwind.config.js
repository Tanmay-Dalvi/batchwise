/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          50: '#F0F7F4',
          100: '#DCEEE6',
          200: '#BBDDCF',
          300: '#8DC4B0',
          400: '#5BA78E',
          500: '#3A8A71',
          600: '#2A6F5A',
          700: '#225848',
          800: '#1B473A',
          900: '#143D2B', // Deep forest primary accent
          950: '#0A2419',
        },
        cream: {
          50: '#FCFBF9',
          100: '#FAF8F5', // Warm off-white background
          200: '#F4EFEA',
          300: '#EAE2D8',
          400: '#D8CCBD',
        },
        charcoal: {
          800: '#2D3136',
          900: '#1C1E21', // Primary text
          950: '#121416',
        },
        limeaccent: {
          DEFAULT: '#84CC16',
          dark: '#65A30D',
          light: '#A3E635',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      }
    },
  },
  plugins: [],
}

