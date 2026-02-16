import 'server-only';
import { cookies } from 'next/headers';
// import { SignJWT, jwtVerify } from 'jose'
// import { SessionPayload } from '@/app/lib/definitions'

/*const secretKey = process.env.SESSION_SECRET
const encodedKey = new TextEncoder().encode(secretKey)

export async function encrypt(payload) {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(encodedKey)
}

export async function decrypt(session = '') {
  try {
    const { payload } = await jwtVerify(session, encodedKey, {
      algorithms: ['HS256'],
    })
    return payload
  } catch (error) {
    console.log('Failed to verify session')
  }
}*/

export async function getToken() {
  const cookieStore = await cookies();
  return cookieStore.get('token')?.value;
}
export async function getTokenWithHandle() {
  const cookieStore = await cookies();
  const token = cookieStore.get('token')?.value;
  const handle = cookieStore.get('handle')?.value;
  return { token, handle };
}

export async function removeToken() {
  const cookieStore = await cookies();
  cookieStore.delete('token');
  cookieStore.delete('handle'); // Also clear the org handle cookie
}

export async function storeServerToken(token: string) {
  const cookieStore = await cookies();
  console.log(`storeToken: ${token}`);
  cookieStore.set('token', token);
}

export async function createSession(token: string) {
  const cookieStore = await cookies();

  cookieStore.set('token', token, {
    httpOnly: true,
    secure: true,
    sameSite: 'lax',
    path: '/',
  });
}
