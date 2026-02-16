import dynamic from 'next/dynamic';

const AppUpgradeModule = dynamic<Record<string, unknown>>(
  () => import('@unpod/modules/AppSubscription/Upgrade'),
);

export async function generateMetadata() {
  return {
    title: 'Upgrade Plan | Unpod',
    description: 'Upgrade your Unpod plan to access premium features.',
  };
}

export default function UpgradePage() {
  return <AppUpgradeModule />;
}
