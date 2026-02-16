import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const token = searchParams.get('token');

  // Get the actual host from headers (handles production correctly)
  const host = req.headers.get('host');
  const protocol = req.headers.get('x-forwarded-proto') || 'https';
  const baseUrl = `${protocol}://${host}`;

  if (!token) {
    return NextResponse.redirect(
      new URL(
        `/auth/email-verified-failed/?error=${encodeURIComponent('Missing token')}`,
        baseUrl,
      ),
    );
  }

  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (process.env.productId) {
      headers['Product-Id'] = process.env.productId;
    }

    const res = await fetch(`${process.env.apiUrl}verify-token/`, {
      method: 'POST',
      body: JSON.stringify({ token }),
      headers,
      cache: 'no-store',
    });

    const response = await res.json();
    const data = response.data;

    if (data?.token) {
      const cookieStore = await cookies();
      cookieStore.set('token', data.token, {
        httpOnly: false,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 30, // 30 days
        path: '/',
      });

      return NextResponse.redirect(new URL('/email-verified/', baseUrl));
    }

    const message = data?.message || response?.message || 'Invalid token';
    return NextResponse.redirect(
      new URL(
        `/auth/email-verified-failed/?error=${encodeURIComponent(message)}`,
        baseUrl,
      ),
    );
  } catch (error: unknown) {
    console.error('[verify-email API] Error:', error);
    const message =
      error instanceof Error
        ? error.message
        : 'Something went wrong during verification';
    return NextResponse.redirect(
      new URL(
        `/auth/email-verified-failed/?error=${encodeURIComponent(message)}`,
        baseUrl,
      ),
    );
  }
}
