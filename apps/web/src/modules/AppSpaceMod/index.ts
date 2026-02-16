import dynamic from 'next/dynamic';

export const AppSpaceRoot = dynamic<any>(
  () => import('@unpod/modules/AppSpace'),
);
export const AppSpaceModule = dynamic<any>(
  () => import('@unpod/modules/AppSpace/View'),
);
