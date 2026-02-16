'use client';
import dynamic from 'next/dynamic';

type AppSpaceModuleProps = {
  tab: unknown;
  id: unknown;
};

const AppSpaceModule = dynamic<AppSpaceModuleProps>(
  () => import('@unpod/modules/AppSpace/View'),
  { ssr: false },
);

export default function SpaceSlugPage() {
  return <AppSpaceModule tab="chat" id={undefined} />;
}
