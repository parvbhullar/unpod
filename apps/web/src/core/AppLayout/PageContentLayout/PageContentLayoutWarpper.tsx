'use client';

import dynamic from 'next/dynamic';
import { useAppSpaceContext } from '@unpod/providers';
import PageContentLayout from '@/core/AppLayout/PageContentLayout';
import type { LayoutProps } from '@/types/common';

const Sidebar = dynamic(
  () => import('@unpod/modules/AppSpace/View/ClassicView/Sidebar'),
  { ssr: false },
);

const PageContentLayoutWrapper = ({ children }: LayoutProps) => {
  const { currentSpace } = useAppSpaceContext();
  const hideSideBar =
    (currentSpace?.final_role === 'guest' &&
      currentSpace?.privacy_type === 'shared') ||
    (currentSpace?.final_role === 'guest' &&
      currentSpace?.privacy_type === 'public') ||
    currentSpace?.token === null ||
    !(
      currentSpace?.content_type === 'general' ||
      currentSpace?.content_type === 'email' ||
      currentSpace?.content_type === 'contact'
    );
  return (
    <PageContentLayout sidebar={hideSideBar ? null : <Sidebar />}>
      {children}
    </PageContentLayout>
  );
};
export default PageContentLayoutWrapper;
