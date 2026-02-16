# Unpod Desktop Build Scripts

This directory contains platform-specific build scripts for the Unpod Desktop application (Tauri).

## Prerequisites

### All Platforms

- Node.js 18+ and npm
- Rust toolchain (install from https://rustup.rs/)
- Tauri CLI (installed automatically via npx)

### macOS

- Xcode Command Line Tools: `xcode-select --install`
- For universal builds: Both Intel and Apple Silicon toolchains

### Windows

- Microsoft C++ Build Tools
- WebView2 Runtime (usually pre-installed on Windows 10/11)

### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  file \
  libxdo-dev \
  libssl-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev
```

### Linux (Fedora)

```bash
sudo dnf install webkit2gtk4.1-devel \
  openssl-devel \
  curl \
  wget \
  file \
  libappindicator-gtk3-devel \
  librsvg2-devel
sudo dnf group install "C Development Tools and Libraries"
```

## Build Scripts

### macOS

#### Universal Build (Intel + Apple Silicon)

```bash
# From project root
chmod +x apps/unpod-tauri/scripts/build-macos.sh
./apps/unpod-tauri/scripts/build-macos.sh
```

Creates a universal .dmg and .app that runs on both Intel and Apple Silicon Macs.

#### Intel Only

```bash
chmod +x apps/unpod-tauri/scripts/build-macos-intel.sh
./apps/unpod-tauri/scripts/build-macos-intel.sh
```

#### Apple Silicon Only

```bash
chmod +x apps/unpod-tauri/scripts/build-macos-silicon.sh
./apps/unpod-tauri/scripts/build-macos-silicon.sh
```

### Windows

#### PowerShell (Recommended)

```powershell
# From project root
.\apps\unpod-tauri\scripts\build-windows.ps1
```

#### Batch File (Alternative)

```cmd
# From project root
.\apps\unpod-tauri\scripts\build-windows.bat
```

Creates both .msi and NSIS installers.

### Linux

```bash
# From project root
chmod +x apps/unpod-tauri/scripts/build-linux.sh
./apps/unpod-tauri/scripts/build-linux.sh
```

Creates .deb, .AppImage, and .rpm packages.

### Cross-Platform

#### Auto-Detect and Build

```bash
chmod +x apps/unpod-tauri/scripts/build-all.sh
./apps/unpod-tauri/scripts/build-all.sh
```

Automatically detects your OS and runs the appropriate build script.

#### Debug Build

```bash
chmod +x apps/unpod-tauri/scripts/build-debug.sh
./apps/unpod-tauri/scripts/build-debug.sh
```

Faster builds with debug symbols (for development/testing).

## NPM Scripts

You can also use the npm scripts from the project root:

```bash
# Build for current platform
npm run desktop:build

# Build in debug mode
npm run desktop:build:debug

# Development mode with hot reload
npm run desktop:dev

# Regenerate app icons
npm run desktop:icon
```

## Platform-Specific Build Scripts via NPM

Add these to `package.json` for convenience:

```bash
# macOS
npm run desktop:build:macos

# Windows
npm run desktop:build:windows

# Linux
npm run desktop:build:linux
```

## Output Locations

After building, installers are located in:

### macOS

- `apps/unpod-tauri/src-tauri/target/release/bundle/dmg/` - .dmg installer
- `apps/unpod-tauri/src-tauri/target/release/bundle/macos/` - .app bundle

### Windows

- `apps/unpod-tauri/src-tauri/target/release/bundle/msi/` - .msi installer
- `apps/unpod-tauri/src-tauri/target/release/bundle/nsis/` - NSIS installer

### Linux

- `apps/unpod-tauri/src-tauri/target/release/bundle/deb/` - .deb package
- `apps/unpod-tauri/src-tauri/target/release/bundle/appimage/` - .AppImage
- `apps/unpod-tauri/src-tauri/target/release/bundle/rpm/` - .rpm package

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Desktop Apps

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - uses: dtolnay/rust-toolchain@stable
      - run: npm ci
      - run: ./apps/unpod-tauri/scripts/build-macos.sh
      - uses: actions/upload-artifact@v4
        with:
          name: macos-build
          path: apps/unpod-tauri/src-tauri/target/release/bundle/dmg/*.dmg

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - uses: dtolnay/rust-toolchain@stable
      - run: npm ci
      - run: .\apps\unpod-tauri\scripts\build-windows.ps1
      - uses: actions/upload-artifact@v4
        with:
          name: windows-build
          path: apps/unpod-tauri/src-tauri/target/release/bundle/msi/*.msi

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - uses: dtolnay/rust-toolchain@stable
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y libwebkit2gtk-4.1-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev
      - run: npm ci
      - run: ./apps/unpod-tauri/scripts/build-linux.sh
      - uses: actions/upload-artifact@v4
        with:
          name: linux-build
          path: |
            apps/unpod-tauri/src-tauri/target/release/bundle/deb/*.deb
            apps/unpod-tauri/src-tauri/target/release/bundle/appimage/*.AppImage
```

## Build Optimization

The release builds are optimized in `Cargo.toml`:

- `opt-level = "s"` - Optimize for size
- `lto = true` - Link-time optimization
- `strip = true` - Strip debug symbols
- `codegen-units = 1` - Better optimization

For faster development builds, use `--debug` flag.

## Troubleshooting

### macOS: "App is damaged and can't be opened"

```bash
# Remove quarantine attribute
xattr -cr /path/to/Unpod.app
```

### Windows: Missing WebView2

Download and install: https://developer.microsoft.com/en-us/microsoft-edge/webview2/

### Linux: AppImage won't run

```bash
chmod +x Unpod.AppImage
./Unpod.AppImage
```

### Build fails with "target not found"

Install the required Rust target:

```bash
# macOS Universal
rustup target add x86_64-apple-darwin aarch64-apple-darwin

# Windows
rustup target add x86_64-pc-windows-msvc

# Linux
rustup target add x86_64-unknown-linux-gnu
```

## Code Signing

### macOS

Set signing identity in `tauri.conf.json`:

```json
"macOS": {
  "signingIdentity": "Developer ID Application: Your Name (TEAM_ID)"
}
```

### Windows

Set certificate thumbprint in `tauri.conf.json`:

```json
"windows": {
  "certificateThumbprint": "YOUR_CERT_THUMBPRINT"
}
```

## Support

For issues or questions:

- GitHub: https://github.com/parvbhullar/superpilot/issues
- Email: yogendra@unpod.ai
