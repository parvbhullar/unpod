#!/bin/bash
# Build script for macOS (Intel & Apple Silicon)
set -e

echo "🍎 Building Unpod Desktop for macOS..."

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: This script must be run on macOS"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")/../../.."

# Build the Next.js app for desktop (static export)
echo "📦 Building Next.js application for desktop..."
node apps/unpod-tauri/scripts/build-desktop-static.js

# Navigate to Tauri directory
cd apps/unpod-tauri

# Build for macOS (creates universal binary for Intel + Apple Silicon)
echo "🔨 Building Tauri application..."
npx tauri build --target universal-apple-darwin

echo "✅ Build complete!"
echo "📂 Output location: apps/unpod-tauri/src-tauri/target/release/bundle/"
echo ""
echo "Generated files:"
echo "  - .dmg installer"
echo "  - .app bundle"
ls -lh src-tauri/target/release/bundle/dmg/ 2>/dev/null || true
ls -lh src-tauri/target/release/bundle/macos/ 2>/dev/null || true
