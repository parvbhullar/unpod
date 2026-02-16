import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import AppPostCard from '@unpod/components/modules/AppPostList/AppPostCard';
import { useFetchDataApi } from '@unpod/providers';
import { useRouter } from 'next/navigation';
import { StyledRootContainer } from './index.styled';
import { Button, Row } from 'antd';
import type { Thread } from '@unpod/constants/types';

const SectionTrending = () => {
  const router = useRouter();

  const [{ apiData }] = useFetchDataApi(
    `threads/explore/trending/`,
    [],
    {
      page: 1,
      page_size: 4,
    },
    true,
    true,
  ) as unknown as [{ apiData: Thread[] }, unknown];
  const threads = apiData ?? [];

  const onThreadClick = (thread: Thread) => {
    if (!thread.slug) {
      return;
    }
    const domain = (thread.organization as { domain_handle?: string })
      ?.domain_handle;
    const spaceSlug = (thread.space as { slug?: string })?.slug;
    router.push(`/${domain}/${spaceSlug}/${thread.slug}`);
  };

  const onSeeMoreClick = () => {
    router.push(`/explore`);
  };

  return (
    <AppPageSection bgColor="#f7f7f7" heading="#Trending">
      <StyledRootContainer>
        {threads.map((thread) => (
          <AppPostCard
            key={thread.slug}
            thread={thread}
            onThreadClick={onThreadClick}
          />
        ))}

        <Row align="middle" justify="center">
          <Button
            type="primary"
            shape="round"
            onClick={onSeeMoreClick}
            style={{ marginTop: '20px', minWidth: '33%' }}
          >
            See More
          </Button>
        </Row>
      </StyledRootContainer>
    </AppPageSection>
  );
};

export default SectionTrending;
