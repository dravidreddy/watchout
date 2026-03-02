import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { Toaster } from "sonner";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";

const inter = Inter({
  subsets: ["latin"],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: "Watchout - AI Travel Planner",
  description: "Your AI-powered travel companion for planning amazing trips across India. Discover destinations, plan itineraries, and explore with confidence.",
  keywords: ["travel", "India", "AI", "trip planner", "itinerary", "vacation", "tourism"],
  authors: [{ name: "Watchout" }],
  openGraph: {
    title: "Watchout - AI Travel Planner",
    description: "Plan your perfect Indian adventure with AI",
    type: "website",
  },
};

import { ThemeProvider } from "@/components/theme/ThemeProvider";
import PWAInstallBanner from "@/components/PWAInstallBanner";
import ConnectionStatus from "@/components/ConnectionStatus";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        {/* LCP Font Optimization */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />

        {/* Viewport and display settings */}
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, maximum-scale=5" />
        <meta name="theme-color" content="#000000" />
        <meta name="theme-color" media="(prefers-color-scheme: dark)" content="#000000" />

        {/* PWA Manifest */}
        <link rel="manifest" href="/manifest.json" />

        {/* Apple-specific PWA meta tags */}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Watchout" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />

        {/* Microsoft Tile */}
        <meta name="msapplication-TileColor" content="#000000" />
        <meta name="msapplication-TileImage" content="/icons/icon-144x144.png" />

        {/* Favicon */}
        <link rel="icon" type="image/png" sizes="32x32" href="/icons/icon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/icons/icon-16x16.png" />
      </head>
      <body className={inter.className}>
        <ThemeProvider>
          <ErrorBoundary>
            <AuthProvider>
              {children}
              <Toaster position="top-center" richColors />

              {/* PWA Components */}
              <PWAInstallBanner />
              <ConnectionStatus />
            </AuthProvider>
          </ErrorBoundary>
        </ThemeProvider>

        {/* PWA Initialization */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', () => {
                  navigator.serviceWorker.register('/service-worker.js')
                    .then(reg => console.log('✅ SW registered:', reg.scope))
                    .catch(err => console.error('❌ SW registration failed:', err));
                });
              }
            `,
          }}
        />
      </body>
    </html>
  );
}
