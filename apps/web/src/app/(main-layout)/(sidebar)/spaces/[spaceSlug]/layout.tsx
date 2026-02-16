import AppSpaceContextProvider from '@unpod/providers/AppSpaceContextProvider';

import { getSpaceDetail } from '../actions';
import { getToken } from '@/app/lib/session';
import PageContentLayoutWrapper from '@/core/AppLayout/PageContentLayout/PageContentLayoutWarpper';
import type { LayoutProps, PageProps } from '@/types/common';

export async function generateMetadata({
  params,
}: PageProps<{ spaceSlug: string }>) {
  const { spaceSlug } = await params;
  const space = await getSpaceDetail(spaceSlug);
  return {
    title: space?.name || 'Space',
    description: space?.description,
    openGraph: {
      title: space?.name || 'Space',
      description: space?.description,
      images: space?.space_picture
        ? { url: space?.space_picture, name: space?.name }
        : null,
    },
  };
}

export default async function AppPageLayout({
  params,
  children,
}: LayoutProps & PageProps<{ spaceSlug: string }>) {
  const { spaceSlug } = await params;
  const token = await getToken();
  const space = await getSpaceDetail(spaceSlug);

  return (
    <AppSpaceContextProvider token={token} space={space}>
      <PageContentLayoutWrapper>{children}</PageContentLayoutWrapper>
    </AppSpaceContextProvider>
  );
}
