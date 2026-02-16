#!/bin/bash
# Build script for macOS (Apple Silicon only)
set -e

echo "🍎 Building Unpod Desktop for macOS (Apple Silicon)..."

# Navigate to project root
cd "$(dirname "$0")/../../.."

# Build the Next.js app for desktop
echo "📦 Building Next.js application for desktop..."
npm run build

# Navigate to Tauri directory
cd apps/unpod-tauri

# Build for Apple Silicon Macs only
echo "🔨 Building Tauri application for ARM64..."
npx tauri build --target aarch64-apple-darwin

echo "✅ Build complete!"
echo "📂 Output location: apps/unpod-tauri/src-tauri/target/aarch64-apple-darwin/release/bundle/"
