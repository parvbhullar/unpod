import dynamic from 'next/dynamic';
import { getKnowledgebase } from './actions';
import type { PageProps } from '@/types/common';

const AppKnowledgeBaseModule = dynamic<Record<string, unknown>>(
  () => import('@unpod/modules/AppKnowledgeBase/View'),
);

export async function generateMetadata({
  params,
}: PageProps<{ kbSlug: string }>) {
  const { kbSlug } = await params;
  const knowledgeBase = await getKnowledgebase(kbSlug);
  return {
    title: knowledgeBase?.title || 'Knowledge Bases',
    description: knowledgeBase?.description,
  };
}

export default async function KnowledgeBaseSlugPage({
  params,
}: PageProps<{ kbSlug: string }>) {
  const { kbSlug } = await params;
  const space = await getKnowledgebase(kbSlug);
  const data = {
    knowledgeBase: space,
    headerProps: {
      space,
      isListingPage: space.space_type === 'general',
    },
  };
  return <AppKnowledgeBaseModule {...(data as Record<string, unknown>)} />;
}
