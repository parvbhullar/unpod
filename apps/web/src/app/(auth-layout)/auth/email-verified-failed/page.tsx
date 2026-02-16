import EmailVerifiedFailed from '../../../../modules/auth/EmailVerifiedFailed';

export const metadata = {
  title: 'Email Verification Failed - Unpod',
  description:
    'Verification of your email has failed. Please try again or contact support.',
};

export default function EmailVerifiedFailedPage() {
  return <EmailVerifiedFailed />;
}
