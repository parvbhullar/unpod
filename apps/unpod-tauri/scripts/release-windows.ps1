# PowerShell production release build script for Windows
# Build script for Windows (x64)

Write-Host "🪟 Building Unpod Desktop Release for Windows..." -ForegroundColor Cyan

# Check if running on Windows
if ($PSVersionTable.Platform -and $PSVersionTable.Platform -ne "Win32NT") {
    Write-Host "❌ Error: This script must be run on Windows" -ForegroundColor Red
    exit 1
}

# Navigate to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptPath\..\..\..\"

# Build Next.js
Write-Host "📦 Building Next.js production bundle..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Next.js build failed" -ForegroundColor Red
    exit 1
}

# Navigate to Tauri directory
Set-Location "apps\unpod-tauri"

# Build for Windows x64 (release mode)
Write-Host "🔨 Building Tauri release..." -ForegroundColor Yellow
npx tauri build --target x86_64-pc-windows-msvc

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tauri build failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Release build complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📂 Output location:" -ForegroundColor Cyan
Write-Host "   MSI: src-tauri\target\release\bundle\msi\" -ForegroundColor White
Write-Host "   NSIS: src-tauri\target\release\bundle\nsis\" -ForegroundColor White
Write-Host ""
Write-Host "Generated installers:" -ForegroundColor Yellow

if (Test-Path "src-tauri\target\release\bundle\msi\") {
    Get-ChildItem -Path "src-tauri\target\release\bundle\msi\" -Filter "*.msi" | ForEach-Object {
        $size = "{0:N2} MB" -f ($_.Length / 1MB)
        Write-Host "  ✓ $($_.Name) ($size)" -ForegroundColor Green
    }
}

if (Test-Path "src-tauri\target\release\bundle\nsis\") {
    Get-ChildItem -Path "src-tauri\target\release\bundle\nsis\" -Filter "*.exe" | ForEach-Object {
        $size = "{0:N2} MB" -f ($_.Length / 1MB)
        Write-Host "  ✓ $($_.Name) ($size)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🎉 Ready to distribute!" -ForegroundColor Cyan
