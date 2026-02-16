#!/bin/bash
# Build script for macOS (Intel only)
set -e

echo "🍎 Building Unpod Desktop for macOS (Intel)..."

# Navigate to project root
cd "$(dirname "$0")/../../.."

# Build the Next.js app for desktop (static export)
echo "📦 Building Next.js application for desktop..."
node apps/unpod-tauri/scripts/build-desktop-static.js

# Navigate to Tauri directory
cd apps/unpod-tauri

# Build for Intel Macs only
echo "🔨 Building Tauri application for x86_64..."
npx tauri build --target x86_64-apple-darwin

echo "✅ Build complete!"
echo "📂 Output location: apps/unpod-tauri/src-tauri/target/x86_64-apple-darwin/release/bundle/"
