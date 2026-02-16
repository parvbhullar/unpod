import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function GET() {
  const cookieStore = await cookies();
  cookieStore.delete('token');
  cookieStore.delete('handle');
  return NextResponse.redirect(new URL('/auth/signin', process.env.siteUrl));
}