#!/bin/bash
# Debug build script - faster builds with debug symbols
set -e

echo "🔧 Building Unpod Desktop (Debug Mode)..."

# Navigate to project root
cd "$(dirname "$0")/../../.."

# Build the Next.js app for desktop (static export)
echo "📦 Building Next.js application for desktop..."
node apps/unpod-tauri/scripts/build-desktop-static.js

# Navigate to Tauri directory
cd apps/unpod-tauri

# Build in debug mode
echo "🔨 Building Tauri application (debug)..."
npx tauri build --debug

echo "✅ Debug build complete!"
echo "📂 Output location: apps/unpod-tauri/src-tauri/target/debug/bundle/"

# Try to show bundle contents
if [[ "$OSTYPE" == "darwin"* ]]; then
    ls -lh src-tauri/target/debug/bundle/macos/ 2>/dev/null || true
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    ls -lh src-tauri/target/debug/bundle/deb/ 2>/dev/null || true
    ls -lh src-tauri/target/debug/bundle/appimage/ 2>/dev/null || true
fi
