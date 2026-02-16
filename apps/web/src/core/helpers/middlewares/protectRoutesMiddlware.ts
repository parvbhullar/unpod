import { setAuthToken } from '@unpod/services';
import type { NextRequest } from 'next/server';

export async function protectedRouteMiddleware(
  protectedRoutes: string[],
  request: NextRequest,
): Promise<boolean> {
  if (isProtectedRoute(protectedRoutes, request)) {
    const userToken = request.cookies.get('token')?.value ?? null;
    if (!userToken) {
      return false;
    }
    setAuthToken(userToken);
  }

  return true;
}

export function isProtectedRoute(
  protectedRoutes: string[],
  request: NextRequest,
): boolean {
  return matchPath(protectedRoutes, request.nextUrl.pathname);
}

function matchPath(routes: string[], currentPath: string): boolean {
  for (const route of routes) {
    if (route === currentPath) {
      return true;
    }
    if (currentPath.startsWith(route)) {
      return true;
    }
  }

  return false;
}
