import "./globals.css";
import type { Metadata } from "next";
import { Toaster } from "sonner";
import { SessionProvider } from "next-auth/react";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "Nexus Local RAG",
  description: "Offline RAG with citations"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground antialiased">
        <SessionProvider>
          <Toaster theme="dark" position="bottom-right" richColors />
          <Header />
          <main className="min-h-screen">{children}</main>
        </SessionProvider>
      </body>
    </html>
  );
}
