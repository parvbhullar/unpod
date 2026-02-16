import type { Dispatch, SetStateAction } from 'react';

export type QueryParams = {
  skipReset?: boolean;
  page?: number;
  page_size?: number;
  [key: string]: unknown;
};

export type ApiResponse<T> = {
  data: T;
  message?: string;
  error?: string;
  count?: number;
};

export type UseGetDataResult<T> = [
  {
    loading: boolean;
    apiData: ApiResponse<T>;
    otherData: unknown;
    skip: number;
    isLoadingMore: boolean;
    isRefreshing: boolean;
    initialUrl: string;
  },
  {
    setSkip: Dispatch<SetStateAction<number>>;
    setData: Dispatch<SetStateAction<ApiResponse<T>>>;
    setLoading: Dispatch<SetStateAction<boolean>>;
    setOtherData: Dispatch<SetStateAction<unknown>>;
    updateInitialUrl: (value: string, callApi?: boolean) => void;
    setQueryParams: (params: QueryParams) => void;
    setLoadingMore: Dispatch<SetStateAction<boolean>>;
    setRefreshing: Dispatch<SetStateAction<boolean>>;
    reCallAPI: () => void;
  },
];

export type UsePaginatedDataState<T> = {
  loading: boolean;
  apiData: T;
  extraData: Record<string, unknown>;
  page: number;
  queryParams: QueryParams;
  isLoadingMore: boolean;
  refreshing: boolean;
  initialUrl: string;
  hasMoreRecord: boolean;
};

export type UsePaginatedDataActions<T> = {
  setPage: Dispatch<SetStateAction<number>>;
  setData: Dispatch<SetStateAction<T>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  reCallAPI: () => void;
  setExtraData: Dispatch<SetStateAction<Record<string, unknown>>>;
  updateInitialUrl: Dispatch<SetStateAction<string>>;
  setAllowApiCall: Dispatch<SetStateAction<boolean>>;
  setQueryParams: (params: QueryParams) => void;
  setLoadingMore: Dispatch<SetStateAction<boolean>>;
  setRefreshing: Dispatch<SetStateAction<boolean>>;
};

export type UsePaginatedDataResult<T> = [
  UsePaginatedDataState<T>,
  UsePaginatedDataActions<T>,
];

export type UsePaginatedConnectorDataState<T> = {
  loading: boolean;
  apiData: T;
  page: number;
  count: number;
  isLoadingMore: boolean;
  refreshing: boolean;
  initialUrl: string;
  hasMoreRecord: boolean;
};

export type UsePaginatedConnectorDataActions<T> = {
  setPage: Dispatch<SetStateAction<number>>;
  setData: Dispatch<SetStateAction<T>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  updateInitialUrl: Dispatch<SetStateAction<string>>;
  reCallAPI: () => void;
  setAllowApiCall: Dispatch<SetStateAction<boolean>>;
  setQueryParams: (params: QueryParams) => void;
  setLoadingMore: Dispatch<SetStateAction<boolean>>;
  setRefreshing: Dispatch<SetStateAction<boolean>>;
};

export type UsePaginatedConnectorDataResult<T> = [
  UsePaginatedConnectorDataState<T>,
  UsePaginatedConnectorDataActions<T>,
];
