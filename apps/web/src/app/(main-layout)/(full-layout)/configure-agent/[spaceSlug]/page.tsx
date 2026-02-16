import ConfigureAgent from '../../../../../modules/ConfigureAgent';
import { getPilot, getSpace } from './actions';
import type { PageProps } from '@/types/common';
import type { Pilot, Spaces } from '@unpod/constants/types';
import type { ComponentType } from 'react';

export default async function ConfigureAgentSpacePage({
  params,
}: PageProps<{ spaceSlug: string }>) {
  const { spaceSlug } = await params;

  const spaceDetails = await getSpace(spaceSlug);

  let pilotData: Pilot | null = null;
  const firstPilotHandle = spaceDetails.space?.pilots?.[0]?.handle;
  if (firstPilotHandle) {
    const pilotResponse = await getPilot(firstPilotHandle);
    pilotData = pilotResponse?.pilot;
  }

  const ConfigureAgentAny = ((
    ConfigureAgent as unknown as { default?: ComponentType<any> }
  ).default ?? ConfigureAgent) as ComponentType<any>;
  return (
    <ConfigureAgentAny
      currentSpace={(spaceDetails?.space ?? null) as Spaces | null}
      pilot={pilotData}
    />
  );
}

export async function generateMetadata({
  params,
}: PageProps<{ spaceSlug: string }>) {
  const { spaceSlug } = await params;
  const { space } = await getSpace(spaceSlug);

  return {
    title: `${space?.name || 'Configure Agent'} | Configure Agent`,
    description: space?.description || 'Configure your AI agent',
  };
}
