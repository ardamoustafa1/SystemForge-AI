import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/ws",
        destination: process.env.BACKEND_INTERNAL_URL_WS || "http://backend:8000/api/ws",
      },
    ];
  },
};

export default nextConfig;
