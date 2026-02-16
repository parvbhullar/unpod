#!/bin/bash
# Production release build script for macOS (Universal)
set -e

echo "🍎 Building Unpod Desktop Release for macOS (Universal)..."

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: This script must be run on macOS"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")/../../.."

# Build Next.js production bundle
echo "📦 Building Next.js production bundle..."
npm run build

# Navigate to Tauri directory
cd apps/unpod-tauri

# Build universal macOS release (Intel + Apple Silicon)
echo "🔨 Building Tauri release (universal binary)..."
npx tauri build --target universal-apple-darwin

# Check if build succeeded
if [ -d "src-tauri/target/universal-apple-darwin/release/bundle/macos/Unpod.app" ]; then
    echo "✅ Release build complete!"
    echo ""
    echo "📂 Output location:"
    echo "   App: src-tauri/target/universal-apple-darwin/release/bundle/macos/Unpod.app"

    # Show app size
    APP_SIZE=$(du -sh src-tauri/target/universal-apple-darwin/release/bundle/macos/Unpod.app | cut -f1)
    echo "   Size: $APP_SIZE"

    # Create DMG manually if automatic creation failed
    if [ ! -f "src-tauri/target/universal-apple-darwin/release/bundle/dmg/Unpod_2.0.0_universal.dmg" ]; then
        echo ""
        echo "📀 Creating DMG installer..."
        cd src-tauri/target/universal-apple-darwin/release/bundle/macos/
        hdiutil create -volname "Unpod" -srcfolder Unpod.app -ov -format UDZO ../dmg/Unpod-2.0.0-universal.dmg 2>/dev/null || echo "⚠️  DMG creation skipped (optional)"
        cd ../../../../../../..
    fi

    echo ""
    echo "🎉 Ready to distribute!"
    echo ""
    echo "Next steps:"
    echo "  1. Test: open src-tauri/target/universal-apple-darwin/release/bundle/macos/Unpod.app"
    echo "  2. Sign (optional): codesign --force --deep --sign 'Developer ID' Unpod.app"
    echo "  3. Distribute: Share the .app or .dmg file"
else
    echo "❌ Build failed!"
    exit 1
fi
