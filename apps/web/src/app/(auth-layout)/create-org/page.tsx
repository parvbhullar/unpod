import CreateOrg from '../../../modules/auth/CreateOrg';

export async function generateMetadata() {
  return {
    title: 'Create Organization | Unpod',
    description:
      'Launch a new organization to organize your agents and spaces.',
  };
}

export default function CreateOrgPage() {
  return <CreateOrg />;
}
