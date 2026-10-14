import type { NextConfig } from "next";

const API_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Model generation can take a while on a cold Colab GPU; default proxy timeout is too short.
  experimental: { proxyTimeout: 130_000 },
  // Proxy /api/v1/* to the FastAPI backend (avoids CORS in the browser).
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${API_URL}/api/v1/:path*` }];
  },
};

export default nextConfig;
