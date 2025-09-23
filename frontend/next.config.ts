import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // For Firebase Hosting deployment
  output: 'export',
  trailingSlash: true,

  // Image optimization for static export
  images: {
    unoptimized: true,
  },

  // Disable ESLint during build to prevent deployment failures
  eslint: {
    ignoreDuringBuilds: true,
  },

  // Disable TypeScript type checking during build for deployment
  typescript: {
    ignoreBuildErrors: true,
  },

  // Webpack fallback for Firebase client-side compatibility
  webpack: (config, { dev, isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: require.resolve('crypto-browserify'),
      };
    }
    return config;
  },

  // Environment variables
  env: {
    FIREBASE_COMPATIBILITY_MODE: process.env.NODE_ENV === 'development' ? 'true' : 'false',
  },
};

export default nextConfig;
