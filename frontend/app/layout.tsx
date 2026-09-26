import type { Metadata, Viewport } from "next";
import "./globals.css";
import AppNav from "../components/AppNav";
import ServiceWorker from "../components/ServiceWorker";

export const metadata: Metadata = {
  title: "Attic Reader",
  description: "Photograph or paste Ancient Greek and hear Classical Attic audio.",
  applicationName: "Attic Reader",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: [{ url: "/favicon-32.png", sizes: "32x32", type: "image/png" }],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },
  // iOS: installable from Share → Add to Home Screen, opens without browser chrome.
  appleWebApp: {
    capable: true,
    title: "Attic Reader",
    statusBarStyle: "black-translucent",
  },
  formatDetection: { telephone: false },
  // Next emits mobile-web-app-capable for appleWebApp.capable; older iOS only
  // honours the apple- prefixed tag, so emit that one explicitly too.
  other: {
    "apple-mobile-web-app-capable": "yes",
  },
};

export const viewport: Viewport = {
  themeColor: "#f6f4ee",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,500;0,7..72,600;1,7..72,400&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet" />
      </head>
      <body>
        <AppNav />
        <ServiceWorker />
        {children}
      </body>
    </html>
  );
}
