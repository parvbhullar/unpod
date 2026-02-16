// Migrated from pages/agent-studio/[spaceSlug]/index.jsx to App Route
import dynamic from 'next/dynamic';
import { notFound } from 'next/navigation';
import { getSpaceDetail } from '../actions';
import type { PageProps } from '@/types/common';

const AppSpaceModule = dynamic<Record<string, unknown>>(
  () => import('@unpod/modules/AppAgentModule'),
);

export async function generateMetadata({
  params,
}: PageProps<{ spaceSlug: string }>) {
  const { spaceSlug } = await params;
  const space = await getSpaceDetail(spaceSlug);
  return {
    title: space?.name,
    description: space?.description,
  };
}

export default async function AgentStudioSpacePage({
  params,
}: PageProps<{ spaceSlug: string }>) {
  const { spaceSlug } = await params;
  const space = await getSpaceDetail(spaceSlug);
  if (!space) {
    notFound();
  }
  return <AppSpaceModule {...({ pilot: space } as Record<string, unknown>)} />;
}
