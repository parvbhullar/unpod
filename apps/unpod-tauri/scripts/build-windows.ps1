# PowerShell build script for Windows
# Build script for Windows (x64)

Write-Host "🪟 Building Unpod Desktop for Windows..." -ForegroundColor Cyan

# Check if running on Windows
if ($PSVersionTable.Platform -and $PSVersionTable.Platform -ne "Win32NT") {
    Write-Host "❌ Error: This script must be run on Windows" -ForegroundColor Red
    exit 1
}

# Navigate to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptPath\..\..\..\"

# Build the Next.js app for desktop (static export)
Write-Host "📦 Building Next.js application for desktop..." -ForegroundColor Yellow
node apps\unpod-tauri\scripts\build-desktop-static.js

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Next.js build failed" -ForegroundColor Red
    exit 1
}

# Navigate to Tauri directory
Set-Location "apps\unpod-tauri"

# Build for Windows x64
Write-Host "🔨 Building Tauri application..." -ForegroundColor Yellow
npx tauri build --target x86_64-pc-windows-msvc

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tauri build failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build complete!" -ForegroundColor Green
Write-Host "📂 Output location: apps\unpod-tauri\src-tauri\target\release\bundle\" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated files:" -ForegroundColor Yellow
Get-ChildItem -Path "src-tauri\target\release\bundle\msi\" -ErrorAction SilentlyContinue | Format-Table Name, Length
Get-ChildItem -Path "src-tauri\target\release\bundle\nsis\" -ErrorAction SilentlyContinue | Format-Table Name, Length
