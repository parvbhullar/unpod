#!/bin/bash
# Universal build script - detects OS and builds accordingly
set -e

echo "🚀 Unpod Desktop - Universal Build Script"
echo "=========================================="

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
        echo "Running macOS build script..."
        bash "$SCRIPT_DIR/build-macos.sh"
        ;;
    linux)
        echo "Running Linux build script..."
        bash "$SCRIPT_DIR/build-linux.sh"
        ;;
    windows)
        echo "Running Windows build script..."
        echo "Please use build-windows.bat or build-windows.ps1 directly on Windows"
        exit 1
        ;;
    *)
        echo "❌ Error: Unsupported operating system: $OSTYPE"
        echo "Please use the platform-specific build script:"
        echo "  - macOS: ./scripts/build-macos.sh"
        echo "  - Linux: ./scripts/build-linux.sh"
        echo "  - Windows: .\\scripts\\build-windows.bat or .\\scripts\\build-windows.ps1"
        exit 1
        ;;
esac
