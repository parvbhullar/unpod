import React from 'react';
import { Typography } from 'antd';
import AppPostCard from '@unpod/components/modules/AppPostList/AppPostCard';
import { useFetchDataApi } from '@unpod/providers';
import { useRouter } from 'next/navigation';
import { StyledRootContainer } from './index.styled';
import type { Thread } from '@unpod/constants/types';

const { Title } = Typography;

const BlockTrending = () => {
  const router = useRouter();

  const [{ apiData }] = useFetchDataApi<Thread[]>(
    `threads/explore/trending/`,
    [],
    {
      page: 1,
      page_size: 8,
    },
    true,
    true,
  );
  const threads = apiData ?? [];

  const onThreadClick = (thread: Thread) => {
    if (!thread.slug) {
      return;
    }
    const domain = thread.organization
      ?.domain_handle;
    const spaceSlug = thread.space?.slug;
    router.push(`/${domain}/${spaceSlug}/${thread.slug}`);
  };

  return (
    <StyledRootContainer>
      <Title level={2} className="text-center">
        #Trending
      </Title>

      {threads.map((thread:Thread) => (
        <AppPostCard
          key={thread.slug}
          thread={thread}
          onThreadClick={onThreadClick}
        />
      ))}
    </StyledRootContainer>
  );
};

export default BlockTrending;
