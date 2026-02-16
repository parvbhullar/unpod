import dynamic from 'next/dynamic';

type AppWalletModuleProps = {
  pageTitle: string;
};

const AppWalletModule = dynamic<AppWalletModuleProps>(
  () => import('@unpod/modules/AppWallet'),
);

export const metadata = {
  title: 'Wallet',
  description: 'Manage your wallet and transactions',
  keywords: 'wallet, transactions, balance, manage wallet',
};

export default function WalletPage() {
  return <AppWalletModule pageTitle="wallet.pageTitle" />;
}
