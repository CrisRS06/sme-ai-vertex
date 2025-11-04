import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SME AI - Injection Molding Feasibility Analysis",
  description: "AI-powered injection molding feasibility analysis system. Analyze technical drawings, detect exceptions, and generate comprehensive reports.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
