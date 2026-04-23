import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AuthGate } from "../components/auth-gate";

export const metadata: Metadata = {
  title: "TwinAI Agentic MVP",
  description: "Dashboard for the Agentic AI Ontology MVP.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <AuthGate>{children}</AuthGate>
      </body>
    </html>
  );
}
