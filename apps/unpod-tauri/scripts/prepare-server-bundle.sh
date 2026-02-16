#!/bin/bash

# ============================================
# Prepare Server Bundle for Desktop App
# ============================================
# This script prepares the Next.js standalone build
# to be bundled with the Tauri desktop application

set -e  # Exit on error

echo "=========================================="
echo "Preparing Next.js Server Bundle"
echo "=========================================="

# Get the project root (3 levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
UNPOD_SOCIAL_DIR="$PROJECT_ROOT/apps/web"
TAURI_DIR="$PROJECT_ROOT/apps/unpod-tauri/src-tauri"
SERVER_BUNDLE_DIR="$TAURI_DIR/server"

echo "Project root: $PROJECT_ROOT"
echo "Next.js app: $UNPOD_SOCIAL_DIR"
echo "Server bundle destination: $SERVER_BUNDLE_DIR"
echo ""

# Step 1: Build Next.js in production mode (standalone output)
echo "📦 Step 1: Building Next.js in standalone mode..."
cd "$PROJECT_ROOT"
npm run build 2>&1 | tail -20
echo "✅ Next.js build complete"
echo ""

# Step 2: Check if standalone build exists
# Next.js standalone preserves the full directory structure
STANDALONE_ROOT="$UNPOD_SOCIAL_DIR/.next/standalone"
if [ ! -d "$STANDALONE_ROOT" ]; then
    echo "❌ Error: Standalone build not found at $STANDALONE_ROOT"
    echo "Make sure next.config.js has: output: 'standalone'"
    exit 1
fi

# Find the actual standalone directory (it includes the full path)
# It will be something like: .next/standalone/WebstormProjects/unpod-web
# Look specifically for the apps/web/server.js file (not Next.js internals)
SERVER_JS_PATH=$(find "$STANDALONE_ROOT" -path "*/apps/web/server.js" -not -path "*/node_modules/*" -type f | head -1)
if [ -z "$SERVER_JS_PATH" ]; then
    echo "❌ Error: Could not find server.js"
    echo "Expected to find server.js at */apps/web/server.js under $STANDALONE_ROOT"
    echo "Standalone build may not have been created properly"
    exit 1
fi

# Get the directory 3 levels up from server.js (apps/web/server.js -> ../../..)
STANDALONE_DIR=$(dirname $(dirname $(dirname "$SERVER_JS_PATH")))
if [ ! -d "$STANDALONE_DIR" ]; then
    echo "❌ Error: Could not find standalone build directory"
    echo "Calculated directory: $STANDALONE_DIR"
    exit 1
fi

echo "Found standalone build at: $STANDALONE_DIR"

# Step 3: Clean previous server bundle
echo "🧹 Step 2: Cleaning previous server bundle..."
rm -rf "$SERVER_BUNDLE_DIR"
mkdir -p "$SERVER_BUNDLE_DIR"
echo "✅ Clean complete"
echo ""

# Step 4: Copy standalone server files
echo "📋 Step 3: Copying standalone server files..."

# Copy the entire standalone build
cp -R "$STANDALONE_DIR/"* "$SERVER_BUNDLE_DIR/" 2>/dev/null || true

# Copy .next/static folder (required for Next.js)
mkdir -p "$SERVER_BUNDLE_DIR/apps/web/.next"
if [ -d "$UNPOD_SOCIAL_DIR/.next/static" ]; then
    cp -R "$UNPOD_SOCIAL_DIR/.next/static" "$SERVER_BUNDLE_DIR/apps/web/.next/"
    echo "✅ Copied .next/static"
fi

# Copy public folder if it exists
if [ -d "$UNPOD_SOCIAL_DIR/public" ]; then
    cp -R "$UNPOD_SOCIAL_DIR/public" "$SERVER_BUNDLE_DIR/apps/web/"
    echo "✅ Copied public folder"
fi

echo "✅ Server files copied"
echo ""

# Step 5: Verify the server.js exists
SERVER_JS=$(find "$SERVER_BUNDLE_DIR" -name "server.js" -path "*/apps/web/server.js" -type f | head -1)
if [ ! -f "$SERVER_JS" ]; then
    echo "❌ Error: server.js not found in $SERVER_BUNDLE_DIR"
    echo "Standalone build may not have been created properly"
    exit 1
fi

echo "✅ Verified server.js at: $SERVER_JS"

# Step 6: Create a wrapper server.js at the root
echo "📝 Step 4: Creating wrapper server script..."
cat > "$SERVER_BUNDLE_DIR/server.js" << 'EOF'
#!/usr/bin/env node

// Wrapper script to start the Next.js standalone server
// This runs from the bundled resources directory

const path = require('path');
const fs = require('fs');

// Find the actual server.js file (handles full path preservation in standalone build)
function findServerJs(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
            // Recursively search directories
            const found = findServerJs(fullPath);
            if (found) return found;
        } else if (entry.name === 'server.js' && fullPath.includes('web')) {
            // Found the Next.js server file
            return fullPath;
        }
    }

    return null;
}

const serverPath = findServerJs(__dirname);

if (!serverPath) {
    console.error('Error: Could not find Next.js server.js');
    process.exit(1);
}

console.log('Starting Next.js server from:', serverPath);

// Set environment variables
process.env.NODE_ENV = 'production';
process.env.PORT = process.env.PORT || '3000';
process.env.HOSTNAME = process.env.HOSTNAME || 'localhost';

// Change to the server's directory
process.chdir(path.dirname(serverPath));

// Start the server
require(serverPath);
EOF

chmod +x "$SERVER_BUNDLE_DIR/server.js"
echo "✅ Wrapper script created"
echo ""

# Step 7: Calculate bundle size
BUNDLE_SIZE=$(du -sh "$SERVER_BUNDLE_DIR" | cut -f1)
echo "=========================================="
echo "✅ Server Bundle Ready!"
echo "=========================================="
echo "Bundle location: $SERVER_BUNDLE_DIR"
echo "Bundle size: $BUNDLE_SIZE"
echo "Entry point: $SERVER_BUNDLE_DIR/server.js"
echo ""
echo "The server will start automatically when the desktop app launches."
echo "=========================================="
