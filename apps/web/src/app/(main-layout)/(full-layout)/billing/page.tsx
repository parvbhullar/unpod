import dynamic from 'next/dynamic';

const AppSubscription = dynamic<any>(
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
