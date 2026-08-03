/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'void-bg': '#050505',
        'void-cyan': '#00f3ff',
        'void-blue': '#0066ff',
        'void-panel': 'rgba(10, 10, 15, 0.65)',
        'void-border': 'rgba(0, 243, 255, 0.15)',
      },
      fontFamily: {
        sans: ['Inter', 'Rajdhani', 'sans-serif'],
      },
      backdropBlur: {
        'glass': '12px',
      }
    },
  },
  plugins: [],
}
