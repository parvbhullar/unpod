import dynamic from 'next/dynamic';

export const BridgeMainContent = dynamic<any>(() =>
  import('@unpod/modules/AppSIPBridge').then((mod) => mod.BridgeMainContent),
);
