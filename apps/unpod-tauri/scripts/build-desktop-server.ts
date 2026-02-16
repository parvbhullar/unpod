#!/usr/bin/env node
/**
 * Build script for Tauri desktop app with Next.js standalone server
 * This approach bundles the Next.js server with the Tauri app
 */

import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

const rootDir = path.join(__dirname, '../../..');
const socialAppDir = path.join(rootDir, 'apps/web');
const tauriAppDir = path.join(rootDir, 'apps/unpod-tauri');

console.log('📦 Building Next.js for desktop (standalone server)...\n');

try {
  // Build Next.js in standalone mode
  console.log('🔨 Building Next.js standalone server...\n');
  execSync('npx nx build web', {
    cwd: rootDir,
    stdio: 'inherit',
    env: { ...process.env, NODE_ENV: 'production' },
  });

  // Copy standalone build to Tauri resources
  const standaloneSource = path.join(socialAppDir, '.next/standalone');
  const standaloneDest = path.join(tauriAppDir, 'dist/server');

  console.log('\n📋 Copying standalone server to Tauri dist...');

  // Remove old dist
  const distDir = path.join(tauriAppDir, 'dist');
  if (fs.existsSync(distDir)) {
    fs.rmSync(distDir, { recursive: true, force: true });
  }

  // Create dist directory
  fs.mkdirSync(distDir, { recursive: true });

  // Copy standalone server
  if (fs.existsSync(standaloneSource)) {
    fs.cpSync(standaloneSource, standaloneDest, { recursive: true });
    console.log('✅ Standalone server copied!');
  } else {
    throw new Error(
      'Standalone build not found. Make sure next.config.js has output: "standalone"',
    );
  }

  // Copy static assets
  const staticSource = path.join(socialAppDir, '.next/static');
  const staticDest = path.join(
    standaloneDest,
    'apps/web/.next/static',
  );

  if (fs.existsSync(staticSource)) {
    fs.cpSync(staticSource, staticDest, { recursive: true });
    console.log('✅ Static assets copied!');
  }

  // Copy public directory
  const publicSource = path.join(socialAppDir, 'public');
  const publicDest = path.join(standaloneDest, 'apps/web/public');

  if (fs.existsSync(publicSource)) {
    fs.cpSync(publicSource, publicDest, { recursive: true });
    console.log('✅ Public assets copied!');
  }

  // Create a simple index.html that will be shown while server starts
  const indexHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Unpod</title>
  <style>
    body {
      margin: 0;
      padding: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      font-family: system-ui, -apple-system, sans-serif;
      background: #f5f5f5;
    }
    .loader {
      text-align: center;
    }
    .spinner {
      border: 4px solid #f3f3f3;
      border-top: 4px solid #3498db;
      border-radius: 50%;
      width: 50px;
      height: 50px;
      animation: spin 1s linear infinite;
      margin: 0 auto 20px;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <div class="loader">
    <div class="spinner"></div>
    <h2>Loading Unpod...</h2>
    <p>Starting application server</p>
  </div>
  <script>
    // Redirect to localhost after a short delay
    setTimeout(() => {
      window.location.href = 'http://localhost:3000/desktop/';
    }, 2000);
  </script>
</body>
</html>`;

  fs.writeFileSync(path.join(distDir, 'index.html'), indexHtml);
  console.log('✅ Loader page created!');

  console.log('\n✅ Desktop server build complete!\n');
  console.log(
    '📝 Note: The Tauri app will need to start the Next.js server on launch.',
  );
  console.log(
    '   See apps/unpod-tauri/src-tauri/src/lib.rs for implementation.\n',
  );
} catch (error) {
  const err = error as Error;
  console.error('❌ Build failed:', err.message);
  process.exit(1);
}
