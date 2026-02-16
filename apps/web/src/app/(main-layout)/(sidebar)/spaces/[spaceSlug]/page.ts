import { redirect } from 'next/navigation';
import type { PageProps } from '@/types/common';

export default async function SpaceSlugPage({
  params,
}: PageProps<{ spaceSlug: string }>) {
  const { spaceSlug } = await params;
  return redirect(`/spaces/${spaceSlug}/call`);
}
