import ForgotPassword from '../../../../modules/auth/ForgotPassword';

export const metadata = {
  title: 'Forgot Password - Unpod',
  description: 'Reset your password securely using your registered email.',
};

export default function ForgotPasswordPage() {
  return <ForgotPassword />;
}
