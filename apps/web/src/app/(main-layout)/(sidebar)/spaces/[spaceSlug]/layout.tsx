import type { Metadata } from 'next';
import AppSpaceContextProvider from '@unpod/providers/AppSpaceContextProvider';

import { getSpaceDetail } from '../actions';
import { getToken } from '@/app/lib/session';
import PageContentLayoutWrapper from '@/core/AppLayout/PageContentLayout/PageContentLayoutWarpper';
import type { LayoutProps } from '@/types/common';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ spaceSlug: string }>;
}): Promise<Metadata> {
  const { spaceSlug } = await params;
  const space = await getSpaceDetail(spaceSlug);
  return {
    title: space?.name || 'Space',
    description: space?.description,
    openGraph: {
      title: space?.name || 'Space',
      description: space?.description,
      images: space?.space_picture
        ? [{ url: space?.space_picture, alt: space?.name }]
        : [],
    },
  };
}

export default async function AppPageLayout({
  params,
  children,
}: LayoutProps & { params: Promise<{ spaceSlug: string }> }) {
  const { spaceSlug } = await params;
  const token = await getToken();
  const space = await getSpaceDetail(spaceSlug);

  return (
    <AppSpaceContextProvider token={token} space={space}>
      <PageContentLayoutWrapper>{children}</PageContentLayoutWrapper>
    </AppSpaceContextProvider>
  );
}
