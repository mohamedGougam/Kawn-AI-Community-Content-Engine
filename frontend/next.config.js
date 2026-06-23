/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone is for Docker only; Render Node uses `next start`
  ...(process.env.NEXT_STANDALONE === 'true' ? { output: 'standalone' } : {}),
  reactStrictMode: true,
};

module.exports = nextConfig;
