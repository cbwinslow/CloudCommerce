/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverComponentsExternalPackages: ['puppeteer'],
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  // For Vercel deployment
  output: 'standalone',
  domains: ['cloudcurio.cc'],
};

module.exports = nextConfig;