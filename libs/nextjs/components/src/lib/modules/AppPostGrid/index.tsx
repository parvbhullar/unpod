import type {CSSProperties} from 'react';
import {memo} from 'react';

import {useRouter} from 'next/navigation';
import {onEndReached} from '@unpod/helpers/ListHelper';
import AppGrid from '../../common/AppGrid';
import GridItem from './GridItem';
import type {Thread} from '@unpod/constants/types';

type AppPostGridProps = {
  apiData?: Thread[];
  page?: number;
  setPage?: (page: number) => void;
  loading?: boolean;
  pageSize?: number;
  setData?: (data: Thread[]) => void;
  isLoadingMore?: boolean;
  setLoadingMore?: (loading: boolean) => void;
  containerStyle?: CSSProperties;
  [key: string]: any;
};

const AppPostGrid = ({
                       apiData = [],
                       page = 1,
                       setPage = () => undefined,
                       loading = false,
                       pageSize = 10,
                       setData,
                       isLoadingMore = false,
                       setLoadingMore = () => undefined,
                       containerStyle,
                       ...restProps
                     }: AppPostGridProps) => {
  const router = useRouter();

  const onThreadClick = (thread: Thread) => {
    router.push(`/thread/${thread.slug}`);
  };

  return (
    <div
      style={{
        width: '100%',
        maxWidth: 1050,
        margin: '0 auto',
      }}
    >
      <AppGrid
        itemPadding={16}
        containerStyle={{
          margin: '0 auto',
          ...containerStyle,
        }}
        loading={loading}
        data={apiData}
        responsive={{
          xs: 1,
          sm: 2,
          md: 2,
          lg: 3,
          xl: 3,
          xxl: 3,
        }}
        onEndReached={() => {
          onEndReached(apiData, page, setPage, isLoadingMore, setLoadingMore);
        }}
        renderItem={(thread: Thread, index: number) => {
          return (
            <GridItem
              key={index}
              thread={thread}
              onThreadClick={onThreadClick}
            />
          );
        }}
        {...restProps}
      />
    </div>
  );
};

export default memo(AppPostGrid);
