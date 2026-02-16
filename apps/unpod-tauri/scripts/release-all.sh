#!/bin/bash
# Universal production release script - detects OS and builds release
set -e

echo "🚀 Unpod Desktop - Production Release Builder"
echo "=============================================="
echo ""

# Detect operating system
OS_TYPE="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS_TYPE="windows"
fi

echo "Detected OS: $OS_TYPE"
echo ""

# Navigate to scripts directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

case $OS_TYPE in
    macos)
        echo "Running macOS release build..."
        bash "$SCRIPT_DIR/release-macos.sh"
        ;;
    linux)
        echo "Running Linux release build..."
        bash "$SCRIPT_DIR/release-linux.sh"
        ;;
    windows)
        echo "Running Windows release build..."
        echo "Please use release-windows.ps1 directly on Windows"
        exit 1
        ;;
    *)
        echo "❌ Error: Unsupported operating system: $OSTYPE"
        echo ""
        echo "Please use the platform-specific release script:"
        echo "  - macOS: ./scripts/release-macos.sh"
        echo "  - Linux: ./scripts/release-linux.sh"
        echo "  - Windows: .\\scripts\\release-windows.ps1"
        exit 1
        ;;
esac
