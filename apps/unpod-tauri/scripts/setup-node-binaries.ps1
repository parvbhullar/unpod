# Setup Node.js binaries for Tauri desktop build (Windows)
# This script downloads architecture-specific Node binaries for Windows

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$BINARIES_DIR = Join-Path $SCRIPT_DIR "..\src-tauri\binaries"
$NODE_VERSION = "20.18.2"

Write-Host "=========================================="
Write-Host "Setting up Node.js binaries for Tauri (Windows)"
Write-Host "=========================================="
Write-Host "Node.js version: $NODE_VERSION"
Write-Host "Target directory: $BINARIES_DIR"
Write-Host ""

# Create binaries directory if it doesn't exist
if (-not (Test-Path $BINARIES_DIR)) {
    New-Item -ItemType Directory -Path $BINARIES_DIR -Force | Out-Null
}

Set-Location $BINARIES_DIR

# Download x86_64 (64-bit Intel/AMD) binary if missing
$x64Binary = "node-x86_64-pc-windows-msvc.exe"
if (-not (Test-Path $x64Binary)) {
    Write-Host "📥 Downloading x86_64 (64-bit) Node.js binary..."

    $downloadUrl = "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-win-x64.zip"
    $zipFile = "node-x64.zip"

    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $zipFile -UseBasicParsing

        # Extract the zip
        Expand-Archive -Path $zipFile -DestinationPath "temp-x64" -Force

        # Find and move the node.exe
        $nodeExe = Get-ChildItem -Path "temp-x64" -Recurse -Filter "node.exe" | Select-Object -First 1
        if ($nodeExe) {
            Move-Item -Path $nodeExe.FullName -Destination $x64Binary -Force
            Write-Host "✅ x86_64 binary ready"
        } else {
            Write-Error "node.exe not found in downloaded archive"
        }

        # Cleanup
        Remove-Item -Path $zipFile -Force
        Remove-Item -Path "temp-x64" -Recurse -Force
    }
    catch {
        Write-Error "Failed to download x86_64 binary: $_"
        exit 1
    }
} else {
    Write-Host "✅ x86_64 binary already exists"
}

# Download ARM64 binary if missing (for ARM Windows devices)
$arm64Binary = "node-aarch64-pc-windows-msvc.exe"
if (-not (Test-Path $arm64Binary)) {
    Write-Host "📥 Downloading ARM64 Node.js binary..."

    $downloadUrl = "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-win-arm64.zip"
    $zipFile = "node-arm64.zip"

    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $zipFile -UseBasicParsing

        # Extract the zip
        Expand-Archive -Path $zipFile -DestinationPath "temp-arm64" -Force

        # Find and move the node.exe
        $nodeExe = Get-ChildItem -Path "temp-arm64" -Recurse -Filter "node.exe" | Select-Object -First 1
        if ($nodeExe) {
            Move-Item -Path $nodeExe.FullName -Destination $arm64Binary -Force
            Write-Host "✅ ARM64 binary ready"
        } else {
            Write-Host "⚠️  ARM64 node.exe not found (this is optional)"
        }

        # Cleanup
        Remove-Item -Path $zipFile -Force -ErrorAction SilentlyContinue
        Remove-Item -Path "temp-arm64" -Recurse -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host "⚠️  ARM64 binary download failed (this is optional for most users)"
    }
} else {
    Write-Host "✅ ARM64 binary already exists"
}

# Display summary
Write-Host ""
Write-Host "=========================================="
Write-Host "✅ Setup Complete!"
Write-Host "=========================================="
Get-ChildItem -Path $BINARIES_DIR -Filter "*.exe" | Format-Table Name, @{Name="Size";Expression={"{0:N2} MB" -f ($_.Length / 1MB)}}
Write-Host ""
Write-Host "You can now build the desktop app with:"
Write-Host "  npm run desktop:build"
Write-Host "=========================================="