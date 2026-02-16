import PageContentLayout from '@/core/AppLayout/PageContentLayout';
import dynamic from 'next/dynamic';
import type { LayoutProps } from '@/types/common';

type SidebarProps = {
  path: string;
  title: string;
  idKey?: string;
};

const Sidebar = dynamic<SidebarProps>(
  () => import('@unpod/modules/AppAgentStudio/Sidebar'),
);

export default function BridgeLayout({ children }: LayoutProps) {
  return (
    <PageContentLayout
      sidebar={<Sidebar path="bridges" title="Bridge" idKey="slug" />}
      type="bridge"
    >
      {children}
    </PageContentLayout>
  );
}
