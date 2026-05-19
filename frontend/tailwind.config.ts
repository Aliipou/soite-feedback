import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        kiosk: {
          bg: "#F7F9FC",
          primary: "#2D7D9A",
          "primary-hover": "#256888",
          secondary: "#F0F4F8",
          yes: "#3D9A6A",
          no: "#E85D4A",
          "text-primary": "#1A2332",
          "text-secondary": "#6B7280",
          border: "#E5E7EB",
        },
        scale: {
          1: "#E85D4A",
          2: "#F0934E",
          3: "#F5C842",
          4: "#8BC34A",
          5: "#4CAF50",
        },
        dash: {
          sidebar: "#1E2A3A",
          "sidebar-text": "#E8EDF2",
          bg: "#F8FAFC",
          card: "#FFFFFF",
          accent: "#2D7D9A",
        },
      },
      fontSize: {
        "question": ["1.75rem", { lineHeight: "2.25rem", fontWeight: "600" }],
        "button-lg": ["1.375rem", { lineHeight: "1.75rem", fontWeight: "600" }],
      },
      minHeight: {
        touch: "80px",
        "touch-xl": "100px",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
