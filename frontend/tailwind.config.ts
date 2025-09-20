import type { Config } from "tailwindcss";
import { fontFamily } from "tailwindcss/defaultTheme";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        espresso: "#2e211a",
        sand: "#f7f0e8",
        sandDeep: "#ede0d2",
        sandHover: "#f0e4d9",
        parchment: "#fdf7f0",
        accentOrange: "#e66b3d",
        accentOrangeLight: "rgba(230, 107, 61, 0.12)",
        sage: "#d5e2d0",
        dustyRose: "#f1d8d0",
        warmGray: "#b7a299",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", ...fontFamily.sans],
        serif: ["var(--font-newsreader)", ...fontFamily.serif],
        display: ["var(--font-newsreader)", ...fontFamily.serif],
      },
      boxShadow: {
        "claude-card": "0 20px 45px -25px rgba(49, 33, 20, 0.35)",
        "claude-soft": "0 16px 30px -24px rgba(49, 33, 20, 0.45)",
      },
      backgroundImage: {
        "claude-fade":
          "radial-gradient(circle at 20% 20%, rgba(230,107,61,0.12), transparent 55%), radial-gradient(circle at 80% 10%, rgba(213,226,208,0.16), transparent 60%)",
      },
      borderRadius: {
        xl: "1.75rem",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
