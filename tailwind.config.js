/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/templates/*.{html,js}",
    "./node_modules/tw-elements/js/**/*.js",
  ],
  safelist: ["bg-success", "bg-info", "bg-warning", "bg-danger"],
  theme: {
    extend: {
      fontFamily: {
        "noto-sans": ["Noto Sans", "sans-serif"],
      },
    },
  },
  plugins: [require("tw-elements/plugin.cjs")],
  darkMode: "class",
};
