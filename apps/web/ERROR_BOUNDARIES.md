# Error Boundaries Documentation

This document explains the error boundary implementation in the UnpodWeb application.

## Overview

Error boundaries are React components that catch JavaScript errors anywhere in their child component tree, log those errors, and display a fallback UI instead of crashing the entire application.

## Implementation

The application has multiple layers of error boundaries to handle errors at different levels:

### 1. Global Error Boundary (`/src/app/global-error.js`)

Catches errors in the root layout. This is the last line of defense and will catch errors that bubble up from anywhere in the application.

- **Location**: `/apps/web/src/app/global-error.js`
- **Scope**: Entire application including root layout
- **Features**:
  - Minimal inline styles (no dependencies on app styles)
  - Try again and Go home buttons
  - Logs errors to console

### 2. Root Error Boundary (`/src/app/error.js`)

Catches errors in all routes except errors in the root layout itself.

- **Location**: `/apps/web/src/app/error.js`
- **Scope**: All application routes
- **Features**:
  - Uses Ant Design Result component
  - Retry and Go Home actions
  - Logs errors to console

### 3. Layout Group Error Boundaries

Specific error boundaries for each major layout section:

#### Main Layout (`/src/app/(main-layout)/error.js`)

- **Scope**: All protected application pages
- **Actions**: Retry, Go to Dashboard

#### Auth Layout (`/src/app/(auth-layout)/error.js`)

- **Scope**: Authentication pages (signin, signup, etc.)
- **Actions**: Try Again, Back to Sign In

#### Front Layout (`/src/app/(front-layout)/error.js`)

- **Scope**: Public pages (landing, privacy policy, etc.)
- **Actions**: Retry, Go to Homepage

### 4. Reusable ErrorBoundary Component

A flexible class-based ErrorBoundary component for wrapping individual components.

- **Location**: `@unpod/components` (`libs/components/src/lib/ErrorBoundary`)
- **Type**: React Class Component
- **Usage**: Wrap any client component that needs isolated error handling

## Usage Examples

### Using Next.js File-Based Error Boundaries

Next.js automatically uses `error.js` files in your route folders:

```
app/
├── error.js              # Catches errors in all routes
├── global-error.js       # Catches errors in root layout
├── (main-layout)/
│   ├── error.js         # Catches errors in main layout routes
│   └── dashboard/
│       └── page.js
```

No code needed - Next.js automatically wraps routes with these error boundaries.

### Using the Reusable ErrorBoundary Component

Import and wrap components that need isolated error handling:

```jsx
import { ErrorBoundary } from '@unpod/components';

// Basic usage with default fallback
function MyPage() {
  return (
    <ErrorBoundary>
      <ComponentThatMightError />
    </ErrorBoundary>
  );
}

// Custom title and description
function MyPage() {
  return (
    <ErrorBoundary
      title="Failed to load agents"
      description="We couldn't load your AI agents. Please try again."
      resetText="Reload Agents"
    >
      <AgentList />
    </ErrorBoundary>
  );
}

// Custom fallback UI
function MyPage() {
  return (
    <ErrorBoundary
      fallback={(error, reset) => (
        <div>
          <h2>Custom Error UI</h2>
          <p>{error.message}</p>
          <button onClick={reset}>Retry</button>
        </div>
      )}
    >
      <ComplexComponent />
    </ErrorBoundary>
  );
}

// With error callback
function MyPage() {
  const handleError = (error, errorInfo) => {
    // Send to error tracking service
    console.error('Component error:', error, errorInfo);
  };

  return (
    <ErrorBoundary onError={handleError}>
      <CriticalComponent />
    </ErrorBoundary>
  );
}

// Show actual error message (useful for development)
function MyPage() {
  return (
    <ErrorBoundary showError={process.env.NODE_ENV === 'development'}>
      <DevelopmentComponent />
    </ErrorBoundary>
  );
}
```

### Props for ErrorBoundary Component

| Prop          | Type                  | Default                | Description                                                                      |
|---------------|-----------------------|------------------------|----------------------------------------------------------------------------------|
| `children`    | ReactNode             | -                      | Components to wrap with error boundary                                           |
| `fallback`    | ReactNode \| Function | -                      | Custom fallback UI. Can be a component or function `(error, reset) => ReactNode` |
| `title`       | string                | "Something went wrong" | Title for default fallback UI                                                    |
| `description` | string                | -                      | Description for default fallback UI                                              |
| `resetText`   | string                | "Try Again"            | Text for reset button                                                            |
| `showError`   | boolean               | false                  | Show error message in fallback UI                                                |
| `onError`     | Function              | -                      | Callback when error occurs: `(error, errorInfo) => void`                         |
| `onReset`     | Function              | -                      | Callback when reset button is clicked                                            |

## Error Logging

Currently, all error boundaries log errors to the console. To integrate with an error tracking service:

1. Install error tracking SDK (e.g., Sentry, LogRocket, Bugsnag)
2. Update error logging in each error boundary file
3. Replace `console.error()` with your tracking service's error reporting

Example with Sentry:

```javascript
import * as Sentry from '@sentry/nextjs';

useEffect(() => {
  Sentry.captureException(error);
}, [error]);
```

## Best Practices

1. **Use error boundaries strategically**:
  - Wrap entire page sections to prevent full page crashes
  - Wrap complex components that fetch data
  - Wrap third-party components that might throw errors

2. **Don't overuse**:
  - Don't wrap every single component
  - Error boundaries add overhead
  - Let errors bubble up to page-level boundaries for simple components

3. **Provide context**:
  - Use descriptive titles and messages
  - Include actionable recovery steps
  - Log enough information for debugging

4. **Test error scenarios**:
  - Simulate errors during development
  - Test recovery actions (reset buttons)
  - Verify user experience when errors occur

5. **Event handlers**:
  - Error boundaries do NOT catch errors in event handlers
  - Use try-catch for async operations and event handlers

## Testing Error Boundaries

To test error boundaries in development:

```jsx
// Create a component that throws an error
function ErrorTest() {
  throw new Error('Test error!');
  return <div>This will never render</div>;
}

// Use in your page
<ErrorBoundary>
  <ErrorTest />
</ErrorBoundary>
```

## Files Created

- `/apps/web/src/app/global-error.js`
- `/apps/web/src/app/error.js`
- `/apps/web/src/app/(main-layout)/error.js`
- `/apps/web/src/app/(auth-layout)/error.js`
- `/apps/web/src/app/(front-layout)/error.js`
- `/libs/components/src/lib/ErrorBoundary/index.js`

## Further Reading

- [Next.js Error Handling](https://nextjs.org/docs/app/building-your-application/routing/error-handling)
- [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
