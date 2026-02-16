#!/bin/bash
# Production release build for macOS (Intel only)
set -e

echo "🍎 Building Unpod Desktop Release for macOS (Intel)..."

# Navigate to project root
cd "$(dirname "$0")/../../.."

# Build Next.js
echo "📦 Building Next.js production bundle..."
npm run build

# Navigate to Tauri directory
cd apps/unpod-tauri

# Build for Intel Macs
echo "🔨 Building Tauri release for x86_64..."
npx tauri build --target x86_64-apple-darwin

echo "✅ Build complete!"
echo "📂 Output: src-tauri/target/x86_64-apple-darwin/release/bundle/macos/"
