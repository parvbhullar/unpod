import dynamic from 'next/dynamic';
import type { PageProps } from '@/types/common';

const AppSpaceModule = dynamic<any>(
  () => import('@unpod/modules/AppSpace/View'),
);

export default async function SpaceNotePage({
  params,
}: PageProps<{ spaceSlug: string; id: string }>) {
  const { id } = await params;
  return <AppSpaceModule id={id} tab="note" />;
}
