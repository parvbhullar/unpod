#!/bin/bash
# Build script for Linux (x64)
set -e

echo "🐧 Building Unpod Desktop for Linux..."

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Error: This script must be run on Linux"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")/../../.."

# Build the Next.js app for desktop (static export)
echo "📦 Building Next.js application for desktop..."
node apps/unpod-tauri/scripts/build-desktop-static.js

# Navigate to Tauri directory
cd apps/unpod-tauri

# Build for Linux x64
echo "🔨 Building Tauri application..."
npx tauri build --target x86_64-unknown-linux-gnu

echo "✅ Build complete!"
echo "📂 Output location: apps/unpod-tauri/src-tauri/target/release/bundle/"
echo ""
echo "Generated files:"
ls -lh src-tauri/target/release/bundle/deb/ 2>/dev/null || true
ls -lh src-tauri/target/release/bundle/appimage/ 2>/dev/null || true
ls -lh src-tauri/target/release/bundle/rpm/ 2>/dev/null || true
