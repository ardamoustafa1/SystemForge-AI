import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AppProviders } from "@/app/providers";
import { getEnv } from "@/lib/env";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

const { appName } = getEnv();
export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
  ),
  title: {
    template: `%s | ${appName}`,
    default: appName,
  },
  description: "AI-powered system design workspace for engineering teams.",
  keywords: ["system design", "architecture", "AI", "engineering"],
  authors: [{ name: "SystemForge" }],
  openGraph: {
    type: "website",
    title: appName,
    description: "AI-powered system design workspace for engineering teams.",
    siteName: appName,
    images: [{ url: "/og-image.png" }],
  },
  twitter: {
    card: "summary_large_image",
    title: appName,
    description: "AI-powered system design workspace for engineering teams.",
    images: ["/og-image.png"],
  },
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-icon.png",
  },
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="font-sans antialiased">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
