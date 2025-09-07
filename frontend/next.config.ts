import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Simplified configuration for development stability
  serverExternalPackages: ['firebase-admin'],
  
  // Webpack fallback for Firebase client-side compatibility
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
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
