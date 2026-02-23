import {ReactNode} from 'react';
import ListView from './ListView';
import ListFooter from './ListFooter';
import ListEmptyResult from './ListEmptyResult';

type AppListProps<T> = {
  isLoadingMore?: boolean;
  noDataMessage?: string;
  ListEmptyComponent?: ReactNode;
  ListFooterComponent?: ReactNode;
  data: T[];
  onEndReached?: () => void;
  renderItem: (item: T, index: number) => ReactNode;
  footerProps?: {
    loading?: boolean;
    footerText?: string;
    showCount?: number;
    hasMoreRecord?: boolean;
  };
  [key: string]: unknown;
};

const AppList = <T, >({
                        footerProps,
                        ...props
                      }: AppListProps<T>) => {
  return (
    <ListView<T>
      {...props}
      isLoadingMore={footerProps?.loading}
      ListFooterComponent={
        footerProps || props?.isLoadingMore ? (
          <ListFooter
            count={props?.data?.length}
            showCount={footerProps?.showCount}
            loading={props?.isLoadingMore || footerProps?.loading}
            footerText={footerProps?.footerText}
            hasMoreRecord={footerProps?.hasMoreRecord}
          />
        ) : null
      }
      ListEmptyComponent={<ListEmptyResult {...props}></ListEmptyResult>}
    />
  );
};

export default AppList;
