/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        grid: {
          dark: '#0f172a',
          card: '#1e293b',
          border: '#334155',
          accent: '#3b82f6',
          live: '#22c55e',
          dark_pole: '#ef4444',
          warning: '#f59e0b',
        }
      }
    },
  },
  plugins: [],
}
