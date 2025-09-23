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
        "elevated": "0 32px 64px -12px rgba(49, 33, 20, 0.4), 0 16px 32px -8px rgba(49, 33, 20, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.1)",
        "floating": "0 24px 48px -12px rgba(49, 33, 20, 0.35), 0 12px 24px -6px rgba(49, 33, 20, 0.12), 0 0 0 1px rgba(255, 255, 255, 0.08)",
        "hover-lift": "0 40px 80px -12px rgba(49, 33, 20, 0.5), 0 20px 40px -8px rgba(49, 33, 20, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.15)",
        "super-elevated": "0 50px 100px -10px rgba(49, 33, 20, 0.6), 0 25px 50px -5px rgba(49, 33, 20, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.2)",
        "glass": "0 20px 40px -8px rgba(49, 33, 20, 0.3), 0 8px 16px -4px rgba(49, 33, 20, 0.1), inset 0 1px 0 0 rgba(255, 255, 255, 0.1)",
      },
      backgroundImage: {
        "claude-fade":
          "radial-gradient(circle at 20% 20%, rgba(230,107,61,0.12), transparent 55%), radial-gradient(circle at 80% 10%, rgba(213,226,208,0.16), transparent 60%)",
        "claude-fade-enhanced":
          "radial-gradient(circle at 20% 20%, rgba(230,107,61,0.15), transparent 50%), radial-gradient(circle at 80% 10%, rgba(213,226,208,0.2), transparent 55%), radial-gradient(circle at 50% 90%, rgba(49,33,20,0.03), transparent 70%)",
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
