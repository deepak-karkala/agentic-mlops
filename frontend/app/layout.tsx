import "./globals.css";
import type { ReactNode } from "react";
import type { Metadata } from "next";
import { Inter, Newsreader } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const newsreader = Newsreader({
  subsets: ["latin"],
  style: ["normal"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-newsreader",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Agentic MLOps Platform",
  description: "AI-powered MLOps infrastructure design and code generation",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${newsreader.variable}`}>
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
