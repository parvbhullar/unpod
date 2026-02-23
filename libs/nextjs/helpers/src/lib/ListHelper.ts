import {tablePageSize} from '@unpod/constants';

export type PaginationConfig = {
  onChange: (page: number, pageSize: number) => void;
  position: string;
  pageSize: number;
  showLessItems: boolean;
  count: number;
  current: number;
  showTotal: (total: number, range: [number, number]) => string;
};

export const getPagination = (
  pageSize = tablePageSize,
  currentPage: number | undefined,
  dataCount = 10,
  onShowSizeChange?: (current: number, size: number) => void,
  onPageChange?: (page: number, pageSize: number) => void,
): PaginationConfig | false => {
  if (dataCount <= pageSize && pageSize <= 5) {
    return false;
  }
  return {
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    onChange: onPageChange || (() => {
    }),
    position: 'bottom',
    pageSize: pageSize,
    showLessItems: true,
    count: dataCount,
    current: currentPage || 1,
    showTotal: (total: number, range: [number, number]) =>
      `${range[0]}-${range[1]} of ${total} items`,
  };
};

export const onEndReached = <T>(
  data: T[] | null | undefined,
  page: number,
  setPage: (page: number) => void,
  isLoadingMore: boolean,
  setLoadingMore: (loading: boolean) => void,
  pageSize = tablePageSize,
): void => {
  if (
    data?.length &&
    data.length > 0 &&
    !isLoadingMore &&
    data.length === page * pageSize
  ) {
    setLoadingMore(true);
    setPage(page + 1);
  }
};
