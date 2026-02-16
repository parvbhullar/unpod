import Settings from '@/modules/Org/detail/Settings';

export async function generateMetadata() {
  return {
    title: 'Organization Settings - Unpod',
    description: `Manage branding, preferences, and settings for your organization on Unpod.`,
    openGraph: {
      title: `Organization Settings - Unpod`,
      description: `Manage branding, preferences, and settings for your organization on Unpod.`,
    },
  };
}

export default async function HubSettingsPage() {
  return <Settings />;
}
