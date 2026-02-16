import dynamic from 'next/dynamic';
import type { PageProps } from '@/types/common';

import { getPilot } from './actions';

const AppAgentModule = dynamic<any>(
  () => import('@unpod/modules/AppAgentModule'),
);
export async function generateMetadata({
  params,
}: PageProps<{ pilotSlug: string }>) {
  const { pilotSlug } = await params;
  const { pilot } = await getPilot(pilotSlug);
  return {
    title: pilot?.name || 'AI Agent',
    description: pilot?.description,
    // seoImage={pilot?.logo ? { url: pilot.logo } : null},
    // keywords={pilot?.tags?.toString()}
  };
}

export default async function AiStudioPilotPage({
  params,
}: PageProps<{ pilotSlug: string }>) {
  const { pilotSlug } = await params;
  const data = await getPilot(pilotSlug);
  return <AppAgentModule {...(data as Record<string, unknown>)} />;
}
