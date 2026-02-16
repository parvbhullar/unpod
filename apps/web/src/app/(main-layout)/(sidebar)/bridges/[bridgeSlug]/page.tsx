import dynamic from 'next/dynamic';
import { getBridge } from './actions';
import type { PageProps } from '@/types/common';
import type { ComponentType } from 'react';

const BridgeMainContent = dynamic(() =>
  import('../../../../../modules/Bridges').then((mod) => ({
    default: mod.BridgeMainContent,
  })),
);

export async function generateMetadata({
  params,
}: PageProps<{ bridgeSlug: string }>) {
  const { bridgeSlug } = await params;
  return {
    title: `Bridge - ${bridgeSlug} | Unpod`,
    description: `Details and configuration of the Voice Bridge "${bridgeSlug}" on Unpod.`,
  };
}

export default async function BridgeDetailPage({
  params,
}: PageProps<{ bridgeSlug: string }>) {
  const { bridgeSlug } = await params;
  const data = await getBridge(bridgeSlug);
  const BridgeMainContentAny = ((
    BridgeMainContent as unknown as { default?: ComponentType<any> }
  ).default ?? BridgeMainContent) as ComponentType<any>;
  return <BridgeMainContentAny bridge={data} />;
}
