import dynamic from 'next/dynamic';

const AppKnowledgeBaseRoot = dynamic<Record<string, unknown>>(
  () => import('@unpod/modules/AppKnowledgeBase'),
);

export const metadata = {
  title: 'Knowledge Bases',
};

export default function KnowledgeBasesPage() {
  return <AppKnowledgeBaseRoot />;
}
