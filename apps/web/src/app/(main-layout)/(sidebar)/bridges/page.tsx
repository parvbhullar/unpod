import dynamic from 'next/dynamic';

const BridgeMainContent = dynamic(() =>
  import('../../../../modules/Bridges').then((mod) => ({
    default: mod.BridgeMainContent,
  })),
);

export const metadata = {
  title: 'Voice Bridges | Unpod',
  description:
    'Manage and monitor all your Voice Bridges in one place on Unpod.',
};

export default function BridgesPage() {
  return <BridgeMainContent />;
}
