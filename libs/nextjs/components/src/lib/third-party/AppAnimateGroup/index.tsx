import type { ReactNode } from 'react';

type AppAnimateGroupProps = {
  children?: ReactNode;
  [key: string]: unknown;
};

function AppAnimateGroup({ children }: AppAnimateGroupProps) {
  return <>{children}</>;
}

export default AppAnimateGroup;
