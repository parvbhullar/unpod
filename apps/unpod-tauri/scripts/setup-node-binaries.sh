#!/bin/bash
# Setup Node.js binaries for Tauri desktop build
# This script downloads architecture-specific Node binaries and creates a universal binary

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BINARIES_DIR="$SCRIPT_DIR/../src-tauri/binaries"
NODE_VERSION="20.18.2"

echo "=========================================="
echo "Setting up Node.js binaries for Tauri"
echo "=========================================="
echo "Node.js version: $NODE_VERSION"
echo "Target directory: $BINARIES_DIR"
echo ""

# Create binaries directory if it doesn't exist
mkdir -p "$BINARIES_DIR"
cd "$BINARIES_DIR"

# Download ARM64 (Apple Silicon) binary if missing
if [ ! -f "node-aarch64-apple-darwin" ]; then
    echo "📥 Downloading ARM64 (Apple Silicon) Node.js binary..."
    curl -L -o node-arm64.tar.gz "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-darwin-arm64.tar.gz"
    tar -xzf node-arm64.tar.gz
    mv "node-v${NODE_VERSION}-darwin-arm64/bin/node" node-aarch64-apple-darwin
    chmod +x node-aarch64-apple-darwin
    rm -rf "node-v${NODE_VERSION}-darwin-arm64" node-arm64.tar.gz
    echo "✅ ARM64 binary ready"
else
    echo "✅ ARM64 binary already exists"
fi

# Download x86_64 (Intel) binary if missing
if [ ! -f "node-x86_64-apple-darwin" ]; then
    echo "📥 Downloading x86_64 (Intel) Node.js binary..."
    curl -L -o node-x64.tar.gz "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-darwin-x64.tar.gz"
    tar -xzf node-x64.tar.gz
    mv "node-v${NODE_VERSION}-darwin-x64/bin/node" node-x86_64-apple-darwin
    chmod +x node-x86_64-apple-darwin
    rm -rf "node-v${NODE_VERSION}-darwin-x64" node-x64.tar.gz
    echo "✅ x86_64 binary ready"
else
    echo "✅ x86_64 binary already exists"
fi

# Create universal binary
echo "🔨 Creating universal binary..."
lipo -create node-aarch64-apple-darwin node-x86_64-apple-darwin -output node-universal-apple-darwin
chmod +x node-universal-apple-darwin
echo "✅ Universal binary created"
echo ""

# Display summary
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
ls -lh
echo ""
echo "You can now build the desktop app with:"
echo "  npm run desktop:build"
echo "=========================================="