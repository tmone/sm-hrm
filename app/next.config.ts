import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  /* config options here */
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'picsum.photos',
        port: '',
        pathname: '/**',
      },
    ],
  },
  // Add API proxy configuration to forward requests to the FastAPI backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:7860/api/:path*',
      },
      {
        source: '/docs',
        destination: 'http://127.0.0.1:7860/docs',
      },
      {
        source: '/openapi.json',
        destination: 'http://127.0.0.1:7860/openapi.json',
      },
      {
        source: '/static/:path*',
        destination: 'http://127.0.0.1:7860/static/:path*',
      },
    ];
  },
};

export default nextConfig;
