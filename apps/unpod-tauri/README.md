# Unpod Desktop App (Tauri)

Native desktop application for Unpod built with Tauri + Next.js.

## Quick Start

### First Time Setup

See [SETUP.md](./SETUP.md) for detailed prerequisites and installation.

**TL;DR:**

```bash
# Install Rust targets for universal builds
rustup target add x86_64-apple-darwin aarch64-apple-darwin

# Install dependencies
npm install
```

### Development

```bash
# Start development mode (hot reload)
npm run desktop:dev
```

This starts both the Next.js dev server and Tauri desktop app.

### Production Build

```bash
# Build for your current architecture (fast)
cd apps/unpod-tauri
npx tauri build --debug --target aarch64-apple-darwin  # Apple Silicon
# or
npx tauri build --debug --target x86_64-apple-darwin   # Intel

# Universal binary (works on both)
npx tauri build --target universal-apple-darwin
```

## Documentation

- **[SETUP.md](./SETUP.md)** - Prerequisites and installation
- **[README-SIMPLE-BUILD.md](./README-SIMPLE-BUILD.md)** - Quick build guide
- **[DESKTOP-BUILD-FINAL.md](./DESKTOP-BUILD-FINAL.md)** - Complete architecture explanation
- **[BUILD.md](./BUILD.md)** - Comprehensive build documentation
- **[DESKTOP-APPROACH.md](./DESKTOP-APPROACH.md)** - Technical decisions

## Architecture

The desktop app uses a **hybrid architecture**:

```
┌─────────────────────────┐
│   Tauri Desktop App     │  Native window (Rust + WebView)
│   ┌─────────────────┐   │
│   │ Loader HTML     │   │  Loading screen
│   └────────┬────────┘   │
│            ↓             │
│   http://localhost:3000 │  Connects to Next.js
└─────────────────────────┘
            │
            ↓
┌─────────────────────────┐
│   Next.js Server        │  Full web app
│   - SSR                 │  - API routes
│   - Dynamic routes      │  - Real-time features
└─────────────────────────┘
```

**Benefits:**

- ✅ Full Next.js features (SSR, API routes, dynamic routes)
- ✅ No code changes from web version
- ✅ Fast development with hot reload
- ✅ Native desktop window with system integration

**Trade-off:**

- ⚠️ Requires Next.js server running (localhost:3000)

## Project Structure

```
apps/unpod-tauri/
├── src/
│   ├── index.html          # Loader page
│   └── tauri-api.ts        # Tauri API helpers
├── src-tauri/
│   ├── src/
│   │   └── lib.rs          # Rust backend
│   ├── icons/              # App icons
│   ├── Cargo.toml          # Rust dependencies
│   └── tauri.conf.json     # Tauri configuration
├── scripts/                # Build scripts (optional)
└── *.md                    # Documentation
```

## Build Output

After building, find installers in:

- **Debug:** `src-tauri/target/aarch64-apple-darwin/debug/bundle/macos/`
- **Release:** `src-tauri/target/release/bundle/`

### macOS

- `.app` - Application bundle (ready to run!)
- `.dmg` - Disk image installer (may fail in debug mode, not critical)

### Windows

- `.msi` - Windows installer
- `.exe` - NSIS installer

### Linux

- `.deb` - Debian package
- `.AppImage` - Portable app
- `.rpm` - RPM package

## Common Commands

```bash
# Development
npm run desktop:dev                    # Start dev mode
npm run dev                           # Start Next.js only

# Building
cd apps/unpod-tauri
npx tauri build --debug               # Debug build (fast)
npx tauri build                       # Release build
npx tauri build --target universal-apple-darwin  # Universal macOS

# Development tools
npx tauri dev --debug                 # Dev mode with DevTools
npx tauri info                        # Show system info
npx tauri icon <source.png>           # Generate icons
```

## Environment Variables

The desktop app uses the same environment variables as the web app:

- `apiUrl` - Backend API URL
- `chatApiUrl` - WebSocket URL
- `siteUrl` - Frontend URL
- See `apps/web/next.config.js` for all variables

## Features

- ✅ Native desktop window
- ✅ System tray icon
- ✅ Notifications
- ✅ File system access
- ✅ Auto-updates (configured)
- ✅ Deep linking
- ✅ Native menus
- ✅ Window state persistence

## Troubleshooting

### "Target not installed" error

```bash
rustup target add x86_64-apple-darwin aarch64-apple-darwin
```

### "Cannot connect to server"

Make sure Next.js dev server is running:

```bash
npm run dev
```

### Build is slow

Use debug builds and single architecture:

```bash
npx tauri build --debug --target aarch64-apple-darwin
```

### Hot reload not working

Restart both dev server and Tauri:

```bash
npm run desktop:dev
```

### DMG creation fails

This is normal for debug builds. The .app bundle is what matters and it works!
Just run the .app directly:

```bash
open src-tauri/target/aarch64-apple-darwin/debug/bundle/macos/Unpod.app
```

## Contributing

When making changes:

1. Test in dev mode: `npm run desktop:dev`
2. Test debug build before release build
3. Test on both architectures if possible
4. Update documentation

## License

MIT

## Support

- 📧 Email: yogendra@unpod.ai
- 🐛 Issues: https://github.com/parvbhullar/superpilot/issues
- 📖 Tauri Docs: https://tauri.app
