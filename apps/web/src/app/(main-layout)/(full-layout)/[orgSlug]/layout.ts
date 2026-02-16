import { getOrganizationDetail } from './actions';
import type { LayoutProps, PageProps } from '@/types/common';
import type { Organization } from '@unpod/constants/types';

export async function generateMetadata({
  params,
}: PageProps<{ orgSlug: string }>) {
  const { orgSlug } = await params;
  const orgInfo = (await getOrganizationDetail(orgSlug)) as Organization;
  const seoImage = orgInfo?.logo
    ? { url: orgInfo?.logo, name: orgInfo.name }
    : null;

  return {
    title: orgInfo?.name,
    description: orgInfo?.description,
    logo: seoImage,
  };
}

export default function RootOrgLayout({ children }: LayoutProps) {
  return children;
}
