import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { Inter, Fraunces } from "next/font/google";
import { cn } from "@/lib/utils";

const inter = Inter({subsets:['latin'],variable:'--font-sans'});
const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700"],
  style: ["normal", "italic"],
});

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "LearnForge",
  description: "Forge every lesson three ways — plan, layer, and share your class; or learn it, test it, keep it.",
};

function GlassFilters() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true">
      <defs>
        <filter id="glass-distortion-sm" x="0%" y="0%" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.015 0.015" numOctaves={1} seed={7} result="noise" />
          <feGaussianBlur in="noise" stdDeviation={1.5} result="blurred" />
          <feDisplacementMap in="SourceGraphic" in2="blurred" scale={22} xChannelSelector="R" yChannelSelector="G" />
        </filter>
        <filter id="glass-distortion" x="0%" y="0%" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.01 0.01" numOctaves={2} seed={92} result="noise" />
          <feGaussianBlur in="noise" stdDeviation={2} result="blurred" />
          <feDisplacementMap in="SourceGraphic" in2="blurred" scale={55} xChannelSelector="R" yChannelSelector="G" />
        </filter>
        <filter id="glass-distortion-lg" x="0%" y="0%" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.008 0.008" numOctaves={2} seed={47} result="noise" />
          <feGaussianBlur in="noise" stdDeviation={3} result="blurred" />
          <feDisplacementMap in="SourceGraphic" in2="blurred" scale={80} xChannelSelector="R" yChannelSelector="G" />
        </filter>
      </defs>
    </svg>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("font-sans", inter.variable, fraunces.variable)}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <GlassFilters />
        {children}
      </body>
    </html>
  );
}
