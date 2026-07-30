/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: '#2563EB',
          blueHover: '#1D4ED8',
          teal: '#14B8A6',
          emerald: '#10B981',
          indigo: '#6366F1',
          slate: '#64748B',
          bg: '#F8FAFC',
          surface: '#FFFFFF',
          darkSidebar: '#0F172A',
          border: '#E2E8F0',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Fira Code', 'Courier New', 'monospace'],
      }
    },
  },
  plugins: [],
}
