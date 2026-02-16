import { type NextRequest, NextResponse } from 'next/server';
import { protectedRouteMiddleware } from './core/helpers/middlewares/protectRoutesMiddlware';

// Define protected and public routes
const protectedRoutes = [
  '/ai-identity-studio',
  '/ai-studio',
  '/spaces',
  '/bridges',
  '/agent-studio',
  '/configure-agent',
  '/settings',
  '/upgrade',
  '/org',
  '/ai-agents',
  '/call-logs',
  '/api-keys',
  '/shared',
  '/knowledge-bases',
  '/superbooks',
  '/dashboard',
  '/profile',
  '/threads',
  '/thread',
  '/wallet',
  '/agents-connect',
  '/billing',
  '/tags',
  '/seeking',
  '/email-verified',
  '/create-space',
  '/join-org',
  '/create-org',
  '/basic-profile',
  '/ai-identity',
  '/creating-identity',
  '/business-identity',
];

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Define public routes that should be accessible without authentication
  const publicRoutes = [
    '/auth/',
    '/privacy-policy',
    '/terms-and-conditions',
    '/download',
    '/new',
    '/',
  ];

  // Check if current route is public (don't apply auth middleware)
  const isPublicRoute = publicRoutes.some((route) => {
    if (route === '/') {
      return pathname === '/';
    }
    return pathname.startsWith(route);
  });

  if (isPublicRoute) {
    return NextResponse.next();
  }

  //if user has route access for page
  const pageRoutePass = await protectedRouteMiddleware(protectedRoutes, req);
  if (!pageRoutePass) {
    // Prevent redirect loop: only redirect if not already on signin page
    const signInUrl = new URL('/auth/signin', req.url);
    if (pathname !== signInUrl.pathname) {
      // Clear all auth cookies before redirecting to prevent stale auth data
      const response = NextResponse.redirect(signInUrl);
      response.cookies.delete('token');
      response.cookies.delete('handle');
      return response;
    }
    // If already on signin page, let it through
    return NextResponse.next();
  }

  return NextResponse.next();
}

// Matcher configuration for middleware - specifies which routes this middleware applies to
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|.*\\.png$).*)'],
};
