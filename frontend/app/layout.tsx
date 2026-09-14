import type { Metadata, Viewport } from "next";
import "./globals.css";
import AppNav from "../components/AppNav";

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
  themeColor: "#172033",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <AppNav />
        {children}
      </body>
    </html>
  );
}
