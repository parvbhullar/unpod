#!/bin/bash
# Production release build for macOS (Apple Silicon only)
set -e

echo "🍎 Building Unpod Desktop Release for macOS (Apple Silicon)..."

# Navigate to project root
cd "$(dirname "$0")/../../.."

# Build Next.js
echo "📦 Building Next.js production bundle..."
npm run build

# Navigate to Tauri directory
cd apps/unpod-tauri

# Build for Apple Silicon Macs
echo "🔨 Building Tauri release for ARM64..."
npx tauri build --target aarch64-apple-darwin

echo "✅ Build complete!"
echo "📂 Output: src-tauri/target/aarch64-apple-darwin/release/bundle/macos/"
