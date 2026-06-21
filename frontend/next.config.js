/** @type {import('next').NextConfig} */
const backendUrl = process.env.API_PROXY_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const nextConfig = {
  // Standalone is for Docker only; Render Node uses `next start`
  ...(process.env.NEXT_STANDALONE === 'true' ? { output: 'standalone' } : {}),
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
