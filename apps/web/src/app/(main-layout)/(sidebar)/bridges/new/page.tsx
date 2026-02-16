import dynamic from 'next/dynamic';
const BridgeMainContent = dynamic(() =>
  import('../../../../../modules/Bridges').then((mod) => ({
    default: mod.BridgeMainContent,
  })),
);
export const metadata = {
  title: 'Create New Bridge | Unpod',
  description: 'Create a new Voice Bridge in your Unpod environment.',
};

export default function BridgesNewPage() {
  return <BridgeMainContent isNew />;
}
