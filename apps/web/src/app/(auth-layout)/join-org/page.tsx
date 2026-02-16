import JoinOrg from '../../../modules/auth/JoinOrg';

export async function generateMetadata() {
  return {
    title: 'Join Organization | Unpod',
    description:
      'Join a shared organization on Unpod to collaborate and innovate together.',
  };
}

export default function JoinOrgPage() {
  return <JoinOrg />;
}
