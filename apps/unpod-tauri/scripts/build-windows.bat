@echo off
REM Batch build script for Windows (alternative to PowerShell)

echo 🪟 Building Unpod Desktop for Windows...

REM Navigate to project root
cd /d "%~dp0..\..\..\"

REM Build the Next.js app for desktop (static export)
echo 📦 Building Next.js application for desktop...
call node apps\unpod-tauri\scripts\build-desktop-static.js
if %errorlevel% neq 0 (
    echo ❌ Next.js build failed
    exit /b %errorlevel%
)

REM Navigate to Tauri directory
cd apps\unpod-tauri

REM Build for Windows x64
echo 🔨 Building Tauri application...
call npx tauri build --target x86_64-pc-windows-msvc
if %errorlevel% neq 0 (
    echo ❌ Tauri build failed
    exit /b %errorlevel%
)

echo ✅ Build complete!
echo 📂 Output location: apps\unpod-tauri\src-tauri\target\release\bundle\
dir src-tauri\target\release\bundle\msi\
dir src-tauri\target\release\bundle\nsis\
