import Dashboard from '@/modules/Org/Dashboard';

export async function generateMetadata() {
  return {
    title: `Organization | Overview - Unpod`,
    description: `Explore the main dashboard and modules for your organization on Unpod.`,
    openGraph: {
      title: `Organization Overview - Unpod`,
      description: `Explore the main dashboard and modules for your organization on Unpod.`,
    },
  };
}

export default async function OrgDetailPage() {
  return <Dashboard />;
}
