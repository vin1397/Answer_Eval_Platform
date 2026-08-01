/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#9C8CD4",
        secondary: "#F7F5FF",
        accent: "#7C6AC8",
        surface: "#ECE9F8",
        ink: "#2D2A44",
        dark: {
          surface: "#232136",
          card: "#2A2740",
          ink: "#E7E4F5",
        },
      },
      borderRadius: {
        neo: "18px",
      },
      boxShadow: {
        "neo-flat": "8px 8px 16px #d3cfe9, -8px -8px 16px #ffffff",
        "neo-inset": "inset 6px 6px 12px #d3cfe9, inset -6px -6px 12px #ffffff",
        "neo-pressed": "inset 4px 4px 8px #c9c4e2, inset -4px -4px 8px #ffffff",
        "neo-dark": "8px 8px 16px #1a1829, -8px -8px 16px #2e2a4a",
        "neo-dark-inset": "inset 6px 6px 12px #1a1829, inset -6px -6px 12px #2e2a4a",
      },
      fontFamily: {
        sans: ["'Plus Jakarta Sans'", "'Segoe UI'", "system-ui", "sans-serif"],
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-16px)" },
        },
        fadeUp: {
          "0%": { opacity: 0, transform: "translateY(24px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        fadeUp: "fadeUp 0.6s ease-out both",
      },
    },
  },
  plugins: [],
};
