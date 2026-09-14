/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        forest: {
          DEFAULT: "#0E3B36",
          light: "#155048",
          dark: "#092824",
        },
        gold: {
          DEFAULT: "#C89B4A",
          light: "#DDBB78",
          dark: "#9E7A34",
        },
        paper: "#F7F5F0",
        ink: "#1B1F1D",
        muted: "#6B7570",
        line: "#E1DED4",
        warn: "#B65C2B",
        danger: "#A6382E",
        ok: "#3E7A52",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'IBM Plex Sans'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        lg: "10px",
      },
    },
  },
  plugins: [],
}
