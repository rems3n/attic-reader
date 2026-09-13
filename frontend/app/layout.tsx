import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ancient Greek Reader",
  description: "Photograph or paste Ancient Greek and hear Classical Attic audio.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
