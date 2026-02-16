import { serverFetcher } from '../../../lib/fetcher';

type VerifyResetResult =
  | { success: true; userToken: string }
  | { success: false; redirectTo: string };

export async function verifyResetToken(
  token: string,
): Promise<VerifyResetResult> {
  try {
    const data = await serverFetcher<{ user_token?: string; status?: boolean }>(
      'password/reset/verify/',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
        cache: 'no-store',
      },
    );

    if (data?.user_token && data.status === true) {
      return { success: true, userToken: data.user_token as string };
    }
    return { success: false, redirectTo: '/auth/forgot-password' };
  } catch {
    return { success: false, redirectTo: '/auth/forgot-password' };
  }
}
