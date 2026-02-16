import { redirect } from 'next/navigation';
import type { PageProps } from '@/types/common';

export const metadata = {
  title: 'Verify Email | Unpod',
  description: 'Verifying your email address securely.',
};

export default async function VerifyEmailPage({ searchParams }: PageProps) {
  const resolvedSearchParams = await searchParams;
  const tokenParam = resolvedSearchParams?.token;
  const token =
    typeof tokenParam === 'string'
      ? tokenParam
      : Array.isArray(tokenParam)
        ? tokenParam[0]
        : '';

  // Redirect to API route which can set cookies
  redirect(`/api/verify-email/?token=${encodeURIComponent(token)}`);
}
