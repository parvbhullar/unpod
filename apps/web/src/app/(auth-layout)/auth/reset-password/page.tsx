import { redirect } from 'next/navigation';
import ResetPassword from '../../../../modules/auth/ResetPassword';
import { verifyResetToken } from './actions';
import type { PageProps } from '@/types/common';

export const metadata = {
  title: 'Reset Password - Unpod',
  description: 'Enter a new password after verifying the reset link.',
};

export default async function ResetPasswordPage({ searchParams }: PageProps) {
  const resolvedSearchParams = await searchParams;
  const tokenParam = resolvedSearchParams?.token;
  const token =
    typeof tokenParam === 'string'
      ? tokenParam
      : Array.isArray(tokenParam)
        ? tokenParam[0]
        : undefined;
  if (!token) {
    redirect('/auth/forgot-password');
  }
  const result = await verifyResetToken(token);

  if (!result.success) {
    redirect(result.redirectTo);
  }

  return <ResetPassword token={result.userToken} />;
}
