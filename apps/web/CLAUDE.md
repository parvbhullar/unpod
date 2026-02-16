# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UnpodWeb is a Next.js 16 social communication platform built with Nx monorepo architecture. The application features AI agents, video conferencing (LiveKit), real-time messaging, knowledge bases, and SIP bridge integrations.

The project includes a **Tauri desktop application** (`apps/unpod-tauri`) that wraps the Next.js app in a lightweight native desktop experience.

## Commands

### Development
```bash
# Start dev server for the main app
npx nx dev web

# Start desktop app (Tauri) - recommended for desktop development
npm run desktop:dev

# Build production bundle
npx nx build web

# Build desktop app for production
npm run desktop:build

# Start production server (requires build first)
npx nx start web

# Show all available targets for a project
npx nx show project web

# Visualize project graph
npx nx graph
```

### Desktop App (Tauri)
```bash
# Development with hot reload
npm run desktop:dev

# Production build (creates installers)
npm run desktop:build

# Debug build (faster, includes symbols)
npm run desktop:build:debug

# Regenerate app icons
npm run desktop:icon
```

### Linting
```bash
# Lint the main app
npx nx lint web

# Lint with auto-fix
npx nx lint web -- --fix
```

### Testing
Note: This project currently has no test configuration (`unitTestRunner: "none"` in nx.json generators). Tests should be added if implementing new features that require validation.

## Architecture

### Monorepo Structure

This is an Nx monorepo with workspace organization:
- **apps/web** - Main Next.js application (web & desktop frontend)
- **apps/unpod-tauri** - Tauri desktop application (Rust backend + native wrapper)
- **libs/** - Shared libraries organized by domain

### Library Organization

The codebase uses 14 shared libraries with clear separation of concerns:

1. **libs/nextjs/providers** - React Context providers for state management
   - `AuthContextProvider` - User authentication, active hub, subscriptions
   - `AppContextProvider` - Locale and theme settings
   - `AppInfoViewProvider` - Global notifications and loading states
   - `AppOrgContextProvider` - Organization/workspace context
   - `AppModuleContextProvider` - Feature-specific state
   - `APIHooks` - Custom hooks for API calls (useGetDataApi, postDataApi, etc.)

2. **libs/nextjs/services** - HTTP clients and external service integrations
   - `httpClient` - Main Axios instance with JWT auth (points to apiUrl)
   - `httpLocalClient` - Local API client for token management
   - Firebase configuration

3. **libs/nextjs/components** - Shared React components
   - Common UI components exported via wildcard

4. **libs/nextjs/modules** - Complex feature modules
   - AppAgentModule, AppAgentStudio, AppIdentityAgentModule
   - AppKnowledgeBase, AppPost, AppThread
   - AppSIPBridge, AppSpace, AppSubscription, AppWallet

5. **libs/nextjs/custom-hooks** - Custom React hooks for reusable logic

6. **libs/nextjs/helpers** - Utility functions organized by domain
   - ApiHelper, DateHelper, FormHelper, GlobalHelper
   - PermissionHelper, StringHelper, TableHelper, UrlHelper

7. **libs/nextjs/constants** - Application-wide constants

8. **libs/icons** - SVG icon components

9. **libs/localization** - Internationalization (react-intl)

10. **libs/nextjs/livekit** - Video conferencing SDK integration

11. **libs/nextjs/skeleton** - Loading skeleton components

12. **libs/nextjs/mix** - Shared theme configuration and utilities

13. **libs/nextjs/external-libs** - Third-party library integrations

14. **libs/nextjs/react-data-grid** - Data grid components and utilities

### Routing Structure

Next.js App Router with group-based layouts in `apps/web/src/app/`:

- **(auth-layout)/** - Authentication pages (signin, signup, password reset, create-org, join-org)
- **(front-layout)/** - Public landing pages (privacy policy, terms, contact)
- **(main-layout)/** - Protected application pages
  - **(sidebar)/** - Pages with sidebar (ai-studio, agent-studio, bridges, spaces)
  - **(full-layout)/** - Full-width pages (dashboard, ai-agents, threads, profile, billing, org)
  - **[orgSlug]/** - Dynamic organization routes

Route groups (parentheses) isolate layouts without affecting URL paths.

### State Management

The application uses **React Context API with useReducer** (not Redux). All providers follow this pattern:

```javascript
// State split into separate contexts
const [state, dispatch] = useReducer(reducer, initialState);
<StateContext.Provider value={state}>
  <ActionsContext.Provider value={actions}>
```

Access state via hooks:
```javascript
const { user, activeOrg } = useAuthUser();
const { updateLocale } = useAppActionsContext();
```

### API Integration Pattern

All API calls use custom hooks from `libs/nextjs/providers/src/lib/APIHooks.js`:

**Fetching data:**
```javascript
// Paginated GET request
const [{ loading, apiData, page, hasMoreRecord }, { setPage, setData }] =
  usePaginatedDataApi('/agents', [], { orgSlug: 'my-hub' });

// Simple GET request
const [{ loading, apiData }, { setData, setQueryParams }] =
  useGetDataApi('/spaces/123');
```

**Mutations:**
```javascript
import { postDataApi, putDataApi, deleteDataApi } from '@unpod/providers';
import { useInfoViewActionsContext } from '@unpod/providers';

const infoViewContext = useInfoViewActionsContext();

// POST request with loading indicator
await postDataApi('/agents', infoViewContext, { name: 'My Agent' })
  .then(data => {
    // Handle success
  })
  .catch(error => {
    // Error automatically shown via infoViewContext
  });
```

**HTTP Client Details:**
- Base client: `httpClient` (configured in libs/nextjs/services)
- Headers automatically include: `AppType: 'social'`, `Product-Id: 'unpod.ai'`, `Org-Handle`, `Authorization: JWT {token}`
- 401 responses can trigger automatic logout (currently commented out)

### Component Patterns

**Module Structure:**
```
ModuleName/
├── index.js              # Main component
├── index.styled.js       # Styled components
├── SubComponent/
│   ├── index.js
│   └── index.styled.js
```

**Page Component Pattern:**
```javascript
// pages should be async server components
export async function generateMetadata({ params }) {
  return { title: 'Page Title' };
}

export default async function Page({ params }) {
  // Server-side data fetching if needed
  return <ClientComponent />;
}
```

**Client Components:**
- Add `'use client'` directive at the top of files that use hooks, context, or browser APIs
- Most interactive components in `src/modules/` are client components

### Styling

- **Primary:** styled-components (v6.1.19) with SWC compiler
- **UI Library:** Ant Design v5 with Next.js registry
- **Theme:** Configured in `libs/nextjs/mix/src/lib/theme.js`
- **Global styles:** `apps/web/src/app/reset.css`

### Path Aliases

Inside the app (`apps/web/src`):
```javascript
import Component from '@/modules/Component';  // maps to src/*
```

Importing from libs (from anywhere):
```javascript
import { useAuthUser } from '@unpod/providers';
import { ApiHelper } from '@unpod/helpers';
import { AppPostFooter } from '@unpod/components';
```

Lib package names follow the pattern: `@unpod/{lib-name}` (defined in each lib's tsconfig.json)

### Environment Configuration

Environment variables are defined in `apps/web/next.config.js` under `env`:

```javascript
process.env.apiUrl         // API base URL
process.env.chatApiUrl     // WebSocket URL for chat
process.env.siteUrl        // Frontend URL
process.env.appType        // 'social'
process.env.productId      // 'unpod.ai'
```

Current environment points to QA:
- API: `https://qa1.unpod.tv/api/v1/`
- Chat: `wss://qa1-block-service.unpod.tv/ws/v1/`
- Site: `https://qa2.unpod.tv`

### Key Integrations

- **LiveKit** - Video/audio conferencing (token generation in `src/app/api/token/livekit/route.js`)
- **Firebase** - Authentication and storage
- **Mux** - Video processing and streaming
- **Razorpay** - Payment gateway (test mode)
- **Pusher** - Real-time messaging
- **Monaco Editor** - Code editing features
- **TLDraw** - Whiteboard/drawing functionality

### Proxy & Route Protection

Route protection is implemented in `apps/web/src/proxy.js` (Next.js 16+ convention, renamed from middleware.js):
- Protected routes require authentication (includes /create-org, /join-org, /org, etc.)
- Redirects to `/auth/signin` if not authenticated
- Uses token from cookies for validation

### Image Handling

Configured in `next.config.js` using Next.js 16+ `remotePatterns`:
- Allowed domains: res.cloudinary.com, image.mux.com, ik.imagekit.io, storage.googleapis.com
- SVG support enabled with CSP restrictions
- Minimum cache TTL: 60 seconds
- Uses `remotePatterns` instead of deprecated `domains` config

### Important Notes

- The app uses React 19.2.0 and Next.js 16.0.3 (latest versions)
- All styled-components must be registered via `StyledComponentsRegistry` (already configured)
- Ant Design components require `AntdRegistry` wrapper (already configured)
- The application uses trailing slashes in URLs (`trailingSlash: true`)
- Git redirects: `/gpts` → `/ai-agents` (permanent)
- Main branch for PRs: `main`
- Current working branch: `main-qa-app-router`
