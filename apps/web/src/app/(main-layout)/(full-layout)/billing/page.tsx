import dynamic from 'next/dynamic';

const AppSubscription = dynamic<Record<string, unknown>>(
  () => import('@unpod/modules/AppSubscription'),
);

export async function generateMetadata() {
  return {
    title: 'Billing | Unpod',
    description: 'Choose your Unpod plan to access premium features.',
  };
}

export default function UpgradePage() {
  return <AppSubscription />;
}
