import PageContentLayout from '@/core/AppLayout/PageContentLayout';
import dynamic from 'next/dynamic';
import type { LayoutProps } from '@/types/common';

const Sidebar = dynamic<any>(
  () => import('@unpod/modules/AppAgentStudio/Sidebar'),
);

export default function BridgeLayout({ children }: LayoutProps) {
  return (
    <PageContentLayout
      sidebar={<Sidebar path="agent-studio" title="Agent Studio" />}
      type="agent"
    >
      {children}
    </PageContentLayout>
  );
}
