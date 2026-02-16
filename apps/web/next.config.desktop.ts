import { withNx } from '@nx/next/plugins/with-nx';
import type { WithNxOptions } from '@nx/next/plugins/with-nx';
import path from 'path';

/**
 * Next.js configuration for Tauri Desktop builds
 * This config exports the app as static files for the desktop application
 */

const nextConfig: WithNxOptions = {
  turbopack: {
    root: path.join(__dirname, '../..'),
  },
  // Use standalone output for desktop (bundles Next.js server)
  output: 'standalone',

  // Output directory
  distDir: '.next-desktop',

  // Disable image optimization for faster builds
  images: {
    unoptimized: true,
  },

  // Base path for desktop app
  basePath: '',

  // Transpile antd packages
  transpilePackages: [
    'antd',
    '@ant-design/icons',
    '@ant-design/cssinjs',
    '@ant-design/nextjs-registry',
  ],

  experimental: {
    optimizePackageImports: [
      'antd',
      '@ant-design/icons',
      'react-icons',
      'lodash',
      '@unpod/components',
      '@unpod/helpers',
      '@unpod/icons',
    ],
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

  webpack: (config) => {
    return config;
  },

  nx: {
    svgr: true,
  },

  trailingSlash: true,
  poweredByHeader: false,

  compiler: {
    styledComponents: true,
    removeConsole: {
      exclude: ['error', 'warn'],
    },
  },

  env: {
    appType: process.env.appType,
    noIndex: process.env.noIndex,
    noFollow: process.env.noFollow,
    agoraAppId: process.env.agoraAppId,
    apiUrl: process.env.apiUrl,
    chatApiUrl: process.env.chatApiUrl,
    siteUrl: process.env.siteUrl,
    productId: process.env.productId,
    muxEnvKey: process.env.NEXT_PUBLIC_MUX_ENV_KEY,
    isDevMode: process.env.isDevMode,
    currency: process.env.currency,
    paymentGatewayKey: process.env.paymentGatewayKey,
    ClarityProjectId: process.env.ClarityProjectId,
    GATagId: process.env.GATagId,
  },
};

export default withNx(nextConfig);
