/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "Vazirmatn", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
