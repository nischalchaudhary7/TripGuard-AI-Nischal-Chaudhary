/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17202a",
        line: "#d8dee6",
        panel: "#f6f8fb"
      }
    }
  },
  plugins: []
};

