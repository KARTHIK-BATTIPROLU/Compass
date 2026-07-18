import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        border: "var(--border)",
        ring: "var(--ring)",
        // Midnight Forge palette
        "bg-deep": "var(--bg-deep)",
        "bg-panel": "var(--bg-panel)",
        ember: {
          DEFAULT: "var(--ember)",
          hot: "var(--ember-hot)",
          deep: "var(--ember-deep)",
        },
        steel: "var(--steel)",
        mint: "var(--mint-signal)",
      },
      fontFamily: {
        display: ["var(--font-display)", "serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
