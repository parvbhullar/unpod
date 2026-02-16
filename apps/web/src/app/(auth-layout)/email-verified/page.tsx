import EmailVerified from '../../../modules/auth/EmailVerified';

export async function generateMetadata() {
  return {
    title: 'Email Verified | Unpod',
    description: 'Your email has been successfully verified.',
  };
}

export default function EmailVerifiedPage() {
  return <EmailVerified />;
}
