#!/bin/bash
# Production release build script for Linux (x64)
set -e

echo "🐧 Building Unpod Desktop Release for Linux..."

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Error: This script must be run on Linux"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")/../../.."

# Build Next.js
echo "📦 Building Next.js production bundle..."
npm run build

# Navigate to Tauri directory
cd apps/unpod-tauri

# Build for Linux x64 (release mode)
echo "🔨 Building Tauri release..."
npx tauri build --target x86_64-unknown-linux-gnu

echo "✅ Release build complete!"
echo ""
echo "📂 Output location: src-tauri/target/release/bundle/"
echo ""
echo "Generated packages:"

if [ -d "src-tauri/target/release/bundle/deb" ]; then
    echo "  DEB packages:"
    ls -lh src-tauri/target/release/bundle/deb/*.deb 2>/dev/null | awk '{print "    ✓", $9, "("$5")"}'
fi

if [ -d "src-tauri/target/release/bundle/appimage" ]; then
    echo "  AppImage:"
    ls -lh src-tauri/target/release/bundle/appimage/*.AppImage 2>/dev/null | awk '{print "    ✓", $9, "("$5")"}'
fi

if [ -d "src-tauri/target/release/bundle/rpm" ]; then
    echo "  RPM packages:"
    ls -lh src-tauri/target/release/bundle/rpm/*.rpm 2>/dev/null | awk '{print "    ✓", $9, "("$5")"}'
fi

echo ""
echo "🎉 Ready to distribute!"
