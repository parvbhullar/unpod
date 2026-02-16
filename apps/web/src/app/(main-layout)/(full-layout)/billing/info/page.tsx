import dynamic from 'next/dynamic';

const BillingInfo = dynamic<any>(
  () => import('@unpod/modules/AppSubscription/BillingInfo'),
);

export const metadata = {
  title: 'Billing Info | Unpod',
  description: 'Manage your Unpod account Billing Info and Tax details here.',
};

export default function UserSettingsPage() {
  return <BillingInfo />;
}
