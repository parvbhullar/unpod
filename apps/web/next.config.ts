import { config as dotenvConfig } from 'dotenv';
import { withNx } from '@nx/next/plugins/with-nx';
import type { WithNxOptions } from '@nx/next/plugins/with-nx';
import path from 'path';

// Load root-level .env (override any local .env.local values)
dotenvConfig({ path: path.join(__dirname, '../../.env'), override: true });

const nextConfig: WithNxOptions = {
  turbopack: {
    root: path.join(__dirname, '../..'),
  },
  // Disable React Strict Mode
  reactStrictMode: false,
  // Enable standalone output only in production
  ...(process.env.NODE_ENV === 'production' && { output: 'standalone' }),
  // Transpile antd packages to fix cssinjs HMR issues
  transpilePackages: [
    'antd',
    '@ant-design/icons',
    '@ant-design/cssinjs',
    '@ant-design/nextjs-registry',
  ],
  experimental: {
    // Enable optimizations for better performance - tree-shakes unused exports
    optimizePackageImports: [
      'antd',
      '@ant-design/icons',
      'react-icons',
      'lodash',
      '@unpod/components',
      '@unpod/helpers',
      '@unpod/icons',
    ],
    // Disable static cache to force full rebuild
    ...(process.env.NODE_ENV !== 'production' && {
      isrMemoryCacheSize: 0,
    }),
  },
  // Force no cache in development
  onDemandEntries: {
    // Keep pages in memory longer for better HMR
    maxInactiveAge: 1000 * 60 * 60,
  },
  async redirects() {
    return [
      {
        source: '/gpts',
        destination: '/ai-agents',
        permanent: true,
      },
      {
        source: '/gpts/:path',
        destination: '/ai-agents/:path',
        permanent: true,
      },
    ];
  },
  webpack: (config, { dev }) => {
    // Enhance HMR and disable caching in development
    if (dev) {
      // Disable webpack caching in development
      config.cache = false;

      // Optimize HMR for better performance
      config.watchOptions = {
        ...config.watchOptions,
        poll: 1000, // Check for changes every second
        aggregateTimeout: 300, // Delay rebuild after first change
        ignored: ['**/node_modules', '**/.next', '**/.git'],
      };

      // Enable more aggressive HMR
      config.optimization = {
        ...config.optimization,
        moduleIds: 'named',
        runtimeChunk: 'single',
        removeAvailableModules: false,
        removeEmptyChunks: false,
        splitChunks: false,
      };
    }

    return config;
  },
  nx: {
    // Set this to true if you would like to to use SVGR
    // See: https://github.com/gregberge/svgr
    svgr: true,
  },
  trailingSlash: true,
  // Enable compression only in production
  compress: process.env.NODE_ENV === 'production',
  // Power performance optimizations
  poweredByHeader: false,
  // Generate ETags only in production
  generateEtags: process.env.NODE_ENV === 'production',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'res.cloudinary.com',
      },
      {
        protocol: 'https',
        hostname: 'image.mux.com',
      },
      {
        protocol: 'https',
        hostname: 'ik.imagekit.io',
      },
      {
        protocol: 'https',
        hostname: 'storage.googleapis.com',
      },
    ],
    // Disable image cache in development for instant updates
    minimumCacheTTL: process.env.NODE_ENV === 'production' ? 31536000 : 0,
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    dangerouslyAllowSVG: true,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },
  compiler: {
    // Enables the styled-components SWC transform
    styledComponents: true,
    // Remove console.log in production for smaller bundle
    removeConsole:
      process.env.NODE_ENV === 'production'
        ? { exclude: ['error', 'warn'] }
        : false,
  },
  env: {
    apiUrl: process.env.API_URL,
    productId: process.env.PRODUCT_ID,
    isDevMode: process.env.IS_DEV_MODE,
    currency: process.env.CURRENCY,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    clarityProjectId: process.env.CLARITY_PROJECT_ID,
    GATagId: process.env.GA_TAG_ID,
    enableChecksum: process.env.ENABLE_CHECKSUM || 'false',
    checksumSecret: process.env.CHECKSUM_SECRET || '',
    centrifugoUrl: process.env.CENTRIFUGO_URL,
    muxEnvKey: process.env.MUX_ENV_KEY,
    livekitUrl: process.env.LIVEKIT_URL,
  },
  async headers() {
    const corsHeaders = [
      {
        key: 'Access-Control-Allow-Origin',
        value: 'tauri://localhost',
      },
      {
        key: 'Access-Control-Allow-Methods',
        value: 'GET, POST, PUT, DELETE, OPTIONS',
      },
      {
        key: 'Access-Control-Allow-Headers',
        value: 'X-Requested-With, Content-Type, Authorization',
      },
      {
        key: 'Access-Control-Allow-Credentials',
        value: 'true',
      },
    ];

    // In development, only add CORS headers
    if (process.env.NODE_ENV !== 'production') {
      return [
        {
          source: '/:path*',
          headers: corsHeaders,
        },
      ];
    }

    return [
      {
        // CORS headers for all routes (needed for Tauri desktop app)
        source: '/:path*',
        headers: corsHeaders,
      },
      {
        // Cache static assets for 1 year (production only)
        source: '/:all*(svg|jpg|jpeg|png|gif|ico|webp|avif|woff|woff2)',
        headers: [
          ...corsHeaders,
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        // Cache JS and CSS chunks (production only)
        source: '/_next/static/:path*',
        headers: [
          ...corsHeaders,
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
};

export default withNx(nextConfig);
