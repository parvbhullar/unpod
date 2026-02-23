import type {ComponentType, ReactNode} from 'react';
import {memo} from 'react';

import {Spin} from 'antd';
import {useRouter} from 'next/navigation';
import {onEndReached} from '@unpod/helpers/ListHelper';
import AppPostCard from './AppPostCard';
import {StyledList, StyledRootContainer, StyledRow} from './index.styled';
import type {Thread} from '@unpod/constants/types';

type AppPostListProps = {
  apiData?: Thread[];
  page?: number;
  setPage?: (page: number) => void;
  loading?: boolean;
  isLoadingMore?: boolean;
  setLoadingMore?: (loading: boolean) => void;
};

const AppPostList = ({
                       apiData = [],
                       page = 1,
                       setPage = () => undefined,
                       loading = false,
                       isLoadingMore = false,
                       setLoadingMore = () => undefined,
                     }: AppPostListProps) => {
  const router = useRouter();
  const List = StyledList as unknown as ComponentType<{
    data: Thread[];
    onEndReached?: () => void;
    renderItem: (item: Thread, index: number) => ReactNode;
  }>;

  const onThreadClick = (thread: Thread) => {
    router.push(`/thread/${thread.slug}`);
  };

  if (loading)
    return (
      <StyledRow align="middle" justify="center">
        <Spin/>
      </StyledRow>
    );

  return (
    <StyledRootContainer>
      <List
        onEndReached={() => {
          onEndReached(apiData, page, setPage, isLoadingMore, setLoadingMore);
        }}
        data={apiData}
        renderItem={(thread: Thread, index: number) => (
          <AppPostCard
            key={index}
            thread={thread}
            onThreadClick={onThreadClick}
          />
        )}
      />
    </StyledRootContainer>
  );
};

export default memo(AppPostList);
