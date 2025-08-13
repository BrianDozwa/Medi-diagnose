/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: process.env.NODE_ENV === "development"
          ? [
              {
                key: "Content-Security-Policy",
                value: "script-src 'self' 'unsafe-eval' 'unsafe-inline'; object-src 'none';",
              },
            ]
          : [],
      },
    ];
  },
}

export default nextConfig
