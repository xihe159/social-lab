import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Social Lab - 先演练，再开口",
  description:
    "Social Lab is an AI-powered communication simulation platform for rehearsing difficult conversations before they happen.",
};

export const viewport: Viewport = {
  themeColor: "#f5f1ea",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
