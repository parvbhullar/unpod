import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function GET() {
  // For desktop apps (Tauri), tokens are handled client-side via session storage
  // This endpoint provides cookie-based token as fallback for web
  const cookieStore = await cookies();
  const token = cookieStore.get('token')?.value;
  return NextResponse.json({ token });
}

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as { token?: string };
    const { token } = body;
    if (!token) {
      return NextResponse.json({ error: 'Missing token' }, { status: 400 });
    }
    const cookieStore = await cookies();

    // Set cookie with longer expiration for better persistence
    cookieStore.set('token', token, {
      httpOnly: false,
      secure: false,
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 30, // 30 days
      path: '/',
    });

    return NextResponse.json({ message: 'ok' });
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  }
}

export async function DELETE() {
  const cookieStore = await cookies();
  cookieStore.delete('token');
  return NextResponse.json({ message: 'ok' });
}
