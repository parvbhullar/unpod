import dynamic from 'next/dynamic';

const AppAgentModule = dynamic<any>(
  () => import('@unpod/modules/AppAgentModule'),
);

export const metadata = {
  title: 'Configure Agent',
};

export default function AiStudioPage() {
  return <AppAgentModule />;
}
