import dynamic from 'next/dynamic';

type AppSpaceModuleProps = {
  tab: unknown;
  id: unknown;
};

export const AppSpaceRoot = dynamic<Record<string, unknown>>(
  () => import('@unpod/modules/AppSpace'),
);
export const AppSpaceModule = dynamic<AppSpaceModuleProps>(
  () => import('@unpod/modules/AppSpace/View'),
);
