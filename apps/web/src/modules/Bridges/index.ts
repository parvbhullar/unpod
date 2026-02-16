import dynamic from 'next/dynamic';

export const BridgeMainContent = dynamic<Record<string, unknown>>(() =>
  import('@unpod/modules/AppSIPBridge').then((mod) => mod.BridgeMainContent),
);
