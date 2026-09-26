import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      { source: "/", has: [{ type: "query", key: "reading" }], destination: "/library", permanent: false },
      { source: "/course/review", destination: "/practice/review", permanent: true },
      { source: "/course/skills", destination: "/progress", permanent: true },
      { source: "/course", destination: "/learn", permanent: true },
      ...["lesson/:id", "test/:id", "track/:id", "placement", "credits"].map((path) => ({
        source: `/course/${path}`, destination: `/learn/${path}`, permanent: true,
      })),
      { source: "/vocab/:path*", destination: "/words/:path*", permanent: true },
    ];
  },
  // NEXT_DIST_DIR lets a second build (e.g. an e2e run next to a dev server)
  // live beside the default .next without clobbering it.
  ...(process.env.NEXT_DIST_DIR ? { distDir: process.env.NEXT_DIST_DIR } : {}),
};

export default nextConfig;
