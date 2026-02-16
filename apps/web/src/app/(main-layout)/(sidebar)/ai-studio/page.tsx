import dynamic from 'next/dynamic';

const AppAgentModule = dynamic<Record<string, unknown>>(
  () => import('@unpod/modules/AppAgentModule'),
);

export const metadata = {
  title: 'Configure Agent',
};

export default function AiStudioPage() {
  return <AppAgentModule />;
}
