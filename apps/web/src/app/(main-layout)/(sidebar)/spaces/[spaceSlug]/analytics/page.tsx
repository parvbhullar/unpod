'use client';
import dynamic from 'next/dynamic';

const AppSpaceModule = dynamic<any>(
  () => import('@unpod/modules/AppSpace/View'),
  { ssr: false },
);

export default function SpaceSlugPage() {
  return <AppSpaceModule tab="analytics" id={undefined} />;
}
