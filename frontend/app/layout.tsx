import "./globals.css";
import type { Metadata } from "next";
import { AppProviders } from "@/app/providers";
import { getEnv } from "@/lib/env";

const { appName } = getEnv();
export const metadata: Metadata = {
  title: appName,
  description: "AI-powered system design workspace for engineering teams.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
