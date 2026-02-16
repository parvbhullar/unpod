import InviteVerify from '../../../modules/auth/InviteVerify';

export const metadata = {
  title: 'Verify Invite | Unpod',
  description: 'Verify your invitation to join an organization on Unpod.',
};

export default function VerifyInvitePage() {
  return <InviteVerify />;
}
