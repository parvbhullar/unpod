import Dashboard from '@/modules/Org/Dashboard';

export async function generateMetadata() {
  return {
    title: 'Organization - Unpod',
    description:
      'Access analytics, agents, and performance for your organization on Unpod.',
  };
}

export default async function HubDashboardPage() {
  return <Dashboard />;
}
