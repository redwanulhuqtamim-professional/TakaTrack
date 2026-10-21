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
          DEFAULT: '#059669',
          dark: '#047857',
          light: '#ecfdf5',
        }
      }
    },
  },
  plugins: [],
}
