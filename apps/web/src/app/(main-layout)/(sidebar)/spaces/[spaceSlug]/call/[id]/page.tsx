import dynamic from 'next/dynamic';
import type { PageProps } from '@/types/common';

type AppSpaceModuleProps = {
  tab: unknown;
  id: unknown;
};

const AppSpaceModule = dynamic<AppSpaceModuleProps>(
  () => import('@unpod/modules/AppSpace/View'),
);

export default async function SpaceCallPage({
  params,
}: PageProps<{ id: string }>) {
  const { id } = await params;
  return <AppSpaceModule id={id} tab="call" />;
}
