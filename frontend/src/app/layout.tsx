import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import QueryProvider from "@/providers/QueryProvider";
import ErrorBoundary from "@/components/ui/ErrorBoundary";
import ToastContainer from "@/components/ui/Toast";
import OfflineIndicator from "@/components/ui/OfflineIndicator";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Research Agent",
  description: "Comprehensive research agent powered by AI and multiple academic sources",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ErrorBoundary>
          <QueryProvider>
            <OfflineIndicator />
            {children}
            <ToastContainer />
          </QueryProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
