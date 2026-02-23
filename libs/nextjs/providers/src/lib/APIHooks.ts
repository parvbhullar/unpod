'use client';

import {Dispatch, SetStateAction, useCallback, useEffect, useRef, useState,} from 'react';
import {httpClient, httpLocalClient} from '@unpod/services';
import {isRequestSuccessful, sanitizeData} from '@unpod/helpers/ApiHelper';
import {useInfoViewActionsContext} from './context-provider/AppInfoViewProvider';
import {tablePageSize} from '@unpod/constants';
import {consoleLog, isEmptyObject} from '@unpod/helpers/GlobalHelper';
import {AxiosProgressEvent, AxiosResponse, ResponseType} from 'axios';
import type {
  ApiResponse,
  InfoViewActionsContextType,
  QueryParams,
  UseGetDataResult,
  UsePaginatedConnectorDataResult,
  UsePaginatedDataResult,
} from '@unpod/constants/types';

export const useGetDataApi = <T>(
  url: string,
  initialData?: ApiResponse<T>,
  params: QueryParams = {},
  initialCall = true,
  callbackFun?: (data: ApiResponse<T>) => void,
): UseGetDataResult<T> => {
  if (initialData === undefined) {
    initialData = {} as ApiResponse<T>;
  }

  const [skip, setSkip] = useState(0);
  const {showError} = useInfoViewActionsContext();
  const [initialUrl, setInitialUrl] = useState(url);
  const [allowApiCall, setAllowApiCall] = useState(initialCall);
  const [loading, setLoading] = useState(initialCall);
  const [isLoadingMore, setLoadingMore] = useState(false);
  const [isRefreshing, setRefreshing] = useState(false);
  const [apiData, setData] = useState<ApiResponse<T>>(initialData);
  const [otherData, setOtherData] = useState<unknown>(null);
  const [queryParams, updateQueryParams] = useState<QueryParams>(params);
  const [isResetRequired, setResetRequired] = useState(false);
  const responsePendingRef = useRef(false);
  const didCancelRef = useRef(false);

  const updateInitialUrl = (value: string, callApi = true): void => {
    setInitialUrl(value);
    setAllowApiCall(callApi);
  };

  const reCallAPI = (): void => {
    setQueryParams({...queryParams});
  };

  const setQueryParams = (newQueryParams: QueryParams): void => {
    setLoading(true);
    updateQueryParams((prevState: QueryParams) => ({
      ...prevState,
      ...newQueryParams,
    }));
    setAllowApiCall(true);
    if (Array.isArray(initialData)) {
      if (!newQueryParams.skipReset) {
        setSkip(0);
        setResetRequired(true);
      }
    }
  };

  useEffect(() => {
    didCancelRef.current = false;

    const fetchData = (): void => {
      responsePendingRef.current = true;
      if (
        skip === 0 &&
        ((Array.isArray(apiData) && apiData.length === 0) ||
          !Array.isArray(apiData)) &&
        !isResetRequired
      ) {
        setLoading(true);
      }
      if (queryParams.skipReset) {
        setLoading(true);
      }
      let requestParams: QueryParams = {};
      if (!isEmptyObject(queryParams)) {
        requestParams = {
          ...trimObjectValues(queryParams),
        };
      }
      httpClient
        .get(initialUrl, {params: sanitizeData(requestParams)})
        .then((data: AxiosResponse<ApiResponse<T>>) => {
          consoleLog(initialUrl, data.data);
          responsePendingRef.current = false;
          if (!didCancelRef.current) {
            if (isRequestSuccessful(data.status)) {
              if (Array.isArray(initialData)) {
                setLoadingMore(false);
                setRefreshing(false);
                setData(data.data as ApiResponse<T>);
                if (callbackFun) callbackFun(data.data as ApiResponse<T>);
              } else {
                setData(data.data as ApiResponse<T>);
                if (callbackFun) callbackFun(data.data as ApiResponse<T>);
              }
              setLoading(false);
            } else {
              setLoading(false);
              const responseData = data.data as ApiResponse<T>;
              showError(
                responseData.error
                  ? responseData.error
                  : responseData.message || '',
              );
              setData(initialData);
              if (callbackFun) callbackFun(data.data as ApiResponse<T>);
            }
          }
        })
        .catch(
          (error: {
            message?: string;
            response?: { data?: { message?: string } };
          }) => {
            if (
              error?.message &&
              (error.message.includes('Checksum validation failed') ||
                error.message.includes('timestamp validation failed'))
            ) {
              consoleLog(
                initialUrl,
                'Checksum/timestamp validation error:',
                error,
              );
              showError(
                'Data integrity check failed. Please refresh the page and try again.',
              );
            } else if (error?.response?.data?.message) {
              consoleLog(initialUrl, error.response.data.message);
              showError(error.response.data.message);
            } else {
              showError(error.message || 'An error occurred');
            }
            setLoading(false);
          },
        );
    };
    if (allowApiCall && !responsePendingRef.current) fetchData();
    return () => {
      didCancelRef.current = true;
    };
  }, [initialUrl, skip, queryParams, allowApiCall, isRefreshing]);

  return [
    {
      loading,
      apiData,
      otherData,
      skip,
      isLoadingMore,
      isRefreshing,
      initialUrl,
    },
    {
      setSkip,
      setData,
      setLoading,
      setOtherData,
      updateInitialUrl,
      setQueryParams,
      setLoadingMore,
      setRefreshing,
      reCallAPI,
    },
  ];
};

export const usePaginatedDataApi = <T extends unknown[] = unknown[]>(
  url: string,
  initialData: T = [] as unknown as T,
  params: QueryParams = {},
  initialCall = false,
  noPagination = false,
  reverse = false,
  callbackFun?: (data: T) => void,
  displayError = true,
): UsePaginatedDataResult<T> => {
  const [page, setPage] = useState(1);
  const [initialUrl, updateInitialUrl] = useState(url);
  const [loading, setLoading] = useState(true);
  const [isLoadingMore, setLoadingMore] = useState(false);
  const [allowApiCall, setAllowApiCall] = useState(initialCall);
  const [refreshing, setRefreshing] = useState(false);
  const [apiData, setData] = useState<T>(initialData);
  const [extraData, setExtraData] = useState<Record<string, unknown>>({});
  const [queryParams, updateQueryParams] = useState<QueryParams>(params);
  const [isResetRequired, setResetRequired] = useState(false);
  const [hasMoreRecord, setMoreRecordStatus] = useState(true);
  const {showError} = useInfoViewActionsContext();
  const responsePendingRef = useRef(false);
  const didCancelRef = useRef(false);

  const checkHasMoreRecord = (
    data: unknown[],
    count: number,
    requestParams: QueryParams,
  ): void => {
    if (count > 0) {
      setMoreRecordStatus(data?.length < count);
    } else {
      setMoreRecordStatus(
        data?.length === (requestParams?.page_size || tablePageSize),
      );
    }
  };

  const setQueryParams = (newQueryParams: QueryParams): void => {
    setLoading(true);
    updateQueryParams(newQueryParams);
    setAllowApiCall(true);
    if (newQueryParams?.page) {
      setPage(newQueryParams?.page);
    }
    if (Array.isArray(initialData)) {
      if (!newQueryParams.skipReset) {
        setPage(1);
        setResetRequired(true);
      }
    }
  };

  const reCallAPI = (): void => {
    setAllowApiCall(true);
    setQueryParams({...queryParams});
  };

  useEffect(() => {
    didCancelRef.current = false;

    const fetchData = (): void => {
      responsePendingRef.current = true;
      if (
        page === 1 &&
        ((Array.isArray(apiData) && apiData.length === 0) ||
          !Array.isArray(apiData)) &&
        !isResetRequired
      ) {
        setLoading(true);
      }
      if (queryParams.skipReset) {
        setLoading(true);
      }
      let requestParams: QueryParams = {};
      if (!isEmptyObject(queryParams)) {
        requestParams = {
          ...trimObjectValues(queryParams),
        };
      }
      if (Array.isArray(apiData) && !noPagination) {
        requestParams = {...trimObjectValues(queryParams), page};
      }
      if (!requestParams?.page_size) {
        requestParams.page_size = tablePageSize;
      }
      httpClient
        .get(initialUrl, {params: requestParams})
        .then((data: AxiosResponse<{ data: unknown[]; count?: number }>) => {
          consoleLog(initialUrl, data.data);

          responsePendingRef.current = false;
          if (!didCancelRef.current) {
            if (isRequestSuccessful(data.status)) {
              setLoadingMore(false);
              setRefreshing(false);
              setResetRequired(false);
              let resData = isResetRequired ? initialData : apiData;
              console.log(' apiData****:  ', apiData);
              if (reverse) {
                resData = [...data.data.data].concat([...resData]) as T;
                console.log('reverse: ', resData);
              } else if (page === 1) {
                resData = data.data.data as T;
              } else if (page > 1) {
                resData = (resData as unknown[]).concat(data.data.data) as T;
              }
              checkHasMoreRecord(
                resData as unknown[],
                data?.data?.count || 0,
                requestParams,
              );
              setData(resData);
              setLoading(false);

              const {data: _, ...restData} = data.data;
              setExtraData(restData);
              if (callbackFun) callbackFun(resData);
            } else {
              setLoading(false);
              console.log('Error: ', initialUrl, data);
              const responseData = data.data as unknown as ApiResponse<T>;
              if (displayError)
                showError(
                  responseData.error
                    ? responseData.error
                    : responseData.message || '',
                );
              setData(initialData);
              if (callbackFun) callbackFun(data.data as unknown as T);
            }
          }
        })
        .catch(
          (error: {
            message?: string;
            response?: { data?: { message?: string } };
          }) => {
            if (
              error?.message &&
              (error.message.includes('Checksum validation failed') ||
                error.message.includes('timestamp validation failed'))
            ) {
              consoleLog(
                initialUrl,
                'Checksum/timestamp validation error:',
                error,
              );
              if (displayError) {
                showError(
                  'Data integrity check failed. Please refresh the page and try again.',
                );
              }
              if (callbackFun) callbackFun(error as unknown as T);
            } else if (error?.response?.data?.message) {
              consoleLog(initialUrl, error.response.data.message);
              if (callbackFun) callbackFun(error.response.data as unknown as T);
              if (displayError) showError(error.response.data.message);
            } else {
              if (displayError) showError(error.message || 'An error occurred');
              if (callbackFun) callbackFun(error as unknown as T);
            }
            setLoading(false);
          },
        );
    };
    if (allowApiCall && !responsePendingRef.current) fetchData();
    return () => {
      didCancelRef.current = true;
    };
  }, [initialUrl, allowApiCall, page, queryParams, refreshing]);

  return [
    {
      loading,
      apiData,
      extraData,
      page,
      queryParams,
      isLoadingMore,
      refreshing,
      initialUrl,
      hasMoreRecord,
    },
    {
      setPage,
      setData,
      setLoading,
      reCallAPI,
      setExtraData,
      updateInitialUrl,
      setAllowApiCall,
      setQueryParams,
      setLoadingMore,
      setRefreshing,
    },
  ];
};

export const usePaginatedConnectorDataApi = <T extends unknown[] = unknown[]>(
  url: string,
  initialData: T = [] as unknown as T,
  params: QueryParams = {},
  initialCall = false,
  setSpaceSchema: (schema: unknown) => void,
  noPagination = false,
  reverse = false,
  callbackFun?: (data: unknown) => void,
  displayError = true,
): UsePaginatedConnectorDataResult<T> => {
  const [page, setPage] = useState(1);
  const [initialUrl, updateInitialUrl] = useState(url);
  const [loading, setLoading] = useState(true);
  const [isLoadingMore, setLoadingMore] = useState(false);
  const [allowApiCall, setAllowApiCall] = useState(initialCall);
  const [refreshing, setRefreshing] = useState(false);
  const [apiData, setData] = useState<T>(initialData);
  const [queryParams, updateQueryParams] = useState<QueryParams>(params);
  const [isResetRequired, setResetRequired] = useState(false);
  const [hasMoreRecord, setMoreRecordStatus] = useState(true);
  const {showError} = useInfoViewActionsContext();
  const responsePendingRef = useRef(false);
  const didCancelRef = useRef(false);
  const totalCount = useRef(0);

  const checkHasMoreRecord = (
    data: unknown[],
    count: number,
    requestParams: QueryParams,
  ): void => {
    if (count > 0) {
      setMoreRecordStatus(data?.length < count);
    } else {
      setMoreRecordStatus(
        data?.length === (requestParams?.page_size || tablePageSize),
      );
    }
  };

  const setQueryParams = (newQueryParams: QueryParams): void => {
    setLoading(true);
    updateQueryParams((prevState: QueryParams) => ({
      ...prevState,
      ...newQueryParams,
    }));
    setAllowApiCall(true);
    if (newQueryParams?.page) {
      setPage(newQueryParams?.page);
    }
  };

  const reCallAPI = (): void => {
    setLoading(true);
    setPage(1);
    setQueryParams({...queryParams});
  };

  useEffect(() => {
    didCancelRef.current = false;

    const fetchData = (): void => {
      responsePendingRef.current = true;
      if (
        page === 1 &&
        ((Array.isArray(apiData) && apiData.length === 0) ||
          !Array.isArray(apiData)) &&
        !isResetRequired
      ) {
        setLoading(true);
      }
      if (queryParams.skipReset) {
        setLoading(true);
      }
      let requestParams: QueryParams = {};
      if (!isEmptyObject(queryParams)) {
        requestParams = {
          ...trimObjectValues(queryParams),
        };
      }
      if (Array.isArray(apiData) && !noPagination) {
        requestParams = {...trimObjectValues(queryParams), page};
      }
      console.log('Fetching data with params: ', requestParams, queryParams);

      if (!requestParams?.page_size) {
        requestParams.page_size = tablePageSize;
      }
      console.log('Fetching data with params: ', requestParams, queryParams);
      httpClient
        .get(initialUrl, {params: requestParams})
        .then(
          (
            data: AxiosResponse<{
              data: { data: unknown[]; schema: unknown };
              count?: number;
            }>,
          ) => {
            consoleLog(initialUrl, data.data);

            responsePendingRef.current = false;
            if (!didCancelRef.current) {
              if (isRequestSuccessful(data.status)) {
                setLoadingMore(false);
                setRefreshing(false);
                setResetRequired(false);
                let resData = isResetRequired ? initialData : apiData;
                if (reverse) {
                  resData = [...data.data.data.data].concat([...resData]) as T;
                } else if (page === 1) {
                  resData = data.data.data.data as T;
                } else if (page > 1) {
                  resData = (resData as unknown[]).concat(
                    data.data.data.data,
                  ) as T;
                }
                setSpaceSchema(data.data.data.schema);
                checkHasMoreRecord(
                  resData as unknown[],
                  data?.data?.count || 0,
                  requestParams,
                );
                setData(resData);
                totalCount.current = data?.data?.count || 0;
                setLoading(false);
                if (callbackFun) callbackFun(resData);
              } else {
                setLoading(false);
                console.log('Error: ', initialUrl, data);
                const responseData = data.data as unknown as ApiResponse<T>;
                if (displayError)
                  showError(
                    responseData.error
                      ? responseData.error
                      : responseData.message || '',
                  );
                setData(initialData);
                if (callbackFun) callbackFun(data.data as unknown as T);
              }
            }
          },
        )
        .catch(
          (error: {
            message?: string;
            response?: { data?: { message?: string } };
          }) => {
            if (error?.response?.data?.message) {
              consoleLog(initialUrl, error.response.data.message);
              if (callbackFun) callbackFun(error.response.data);
              if (displayError) showError(error.response.data.message);
            } else {
              if (displayError) showError(error.message || 'An error occurred');
              if (callbackFun) callbackFun(error);
            }
            setLoading(false);
          },
        );
    };
    if (allowApiCall && !responsePendingRef.current) fetchData();
    return () => {
      didCancelRef.current = true;
    };
  }, [initialUrl, page, queryParams, refreshing]);

  return [
    {
      loading,
      apiData,
      page,
      count: totalCount.current,
      isLoadingMore,
      refreshing,
      initialUrl,
      hasMoreRecord,
    },
    {
      setPage,
      setData,
      setLoading,
      updateInitialUrl,
      reCallAPI,
      setAllowApiCall,
      setQueryParams,
      setLoadingMore,
      setRefreshing,
    },
  ];
};

export type UseFetchDataState<T> = {
  loading: boolean;
  apiData: T;
  page: number;
  isLoadingMore: boolean;
  refreshing: boolean;
  initialUrl: string;
  hasMoreRecord: boolean;
};

export type UseFetchDataActions<T> = {
  setPage: Dispatch<SetStateAction<number>>;
  setData: Dispatch<SetStateAction<T>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  reCallAPI: () => void;
  updateInitialUrl: (value: string, callApi?: boolean) => void;
  setQueryParams: (params: QueryParams) => void;
  setAllowApiCall: Dispatch<SetStateAction<boolean>>;
  setLoadingMore: Dispatch<SetStateAction<boolean>>;
  setRefreshing: Dispatch<SetStateAction<boolean>>;
};

export type UseFetchDataResult<T> = [
  UseFetchDataState<T>,
  UseFetchDataActions<T>,
];

export const useFetchDataApi = <T>(
  url: string,
  initialData: T,
  params: QueryParams = {},
  initialCall = true,
  noPagination = false,
  reverse = false,
): UseFetchDataResult<T> => {
  const [page, setPage] = useState(1);
  const [initialUrl, setInitialUrl] = useState(url);
  const {showError} = useInfoViewActionsContext();
  const [allowApiCall, setAllowApiCall] = useState(initialCall);
  const [loading, setLoading] = useState(true);
  const [isLoadingMore, setLoadingMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [apiData, setData] = useState<T>(initialData);
  const [queryParams, updateQueryParams] = useState<QueryParams>(params);
  const [isResetRequired, setResetRequired] = useState(false);
  const [hasMoreRecord, setMoreRecordStatus] = useState(true);
  const responsePendingRef = useRef(false);
  const didCancelRef = useRef(false);

  const updateInitialUrl = (value: string, callApi = true): void => {
    setPage(1);
    setAllowApiCall(callApi);
    setInitialUrl(value);
  };

  const reCallAPI = (): void => {
    setLoading(true);
    setPage(1);
    setQueryParams({...queryParams});
  };

  const checkHasMoreRecord = (data: unknown[]): void => {
    let perPageItems = 10;
    if (Object.prototype.hasOwnProperty.call(params, 'limit'))
      perPageItems = params.limit as number;

    setMoreRecordStatus(data.length === perPageItems);
  };

  const setQueryParams = (newQueryParams: QueryParams): void => {
    setPage(1);
    updateQueryParams({...newQueryParams});
    setAllowApiCall(true);
    if (Array.isArray(initialData)) {
      if (!newQueryParams.skipReset) {
        setResetRequired(true);
      }
    }
  };

  useEffect(() => {
    didCancelRef.current = false;

    const fetchData = (): void => {
      responsePendingRef.current = true;
      if (
        page === 1 &&
        ((Array.isArray(apiData) && apiData.length === 0) ||
          !Array.isArray(apiData)) &&
        !isResetRequired
      ) {
        setLoading(true);
      }
      if (queryParams.skipReset) {
        setLoading(true);
      }
      let requestParams: QueryParams = {};
      if (!isEmptyObject(queryParams)) {
        requestParams = {...queryParams};
      }
      if (Array.isArray(apiData) && !noPagination) {
        requestParams = {...queryParams, page, page_size: tablePageSize};
      }

      httpClient
        .get(initialUrl, {params: requestParams})
        .then((data: AxiosResponse<{ data: unknown[] }>) => {
          responsePendingRef.current = false;
          if (!didCancelRef.current) {
            if (isRequestSuccessful(data.status)) {
              if (Array.isArray(initialData)) {
                checkHasMoreRecord(data.data.data);
                setLoadingMore(false);
                setRefreshing(false);
                setResetRequired(false);
                let resData = isResetRequired ? initialData : apiData;
                if (reverse) {
                  resData = [...data.data.data].concat([
                    ...(resData as unknown[]),
                  ]) as T;
                } else if (page === 1) {
                  resData = data.data.data as T;
                } else if (page > 1) {
                  resData = (resData as unknown[]).concat(data.data.data) as T;
                }
                setData(resData);
              } else {
                setData(data.data.data as T);
              }
              setLoading(false);
            } else {
              setLoading(false);
              const responseData = data.data as unknown as ApiResponse<T>;
              showError(
                responseData.error
                  ? responseData.error
                  : responseData.message || '',
              );
              setData(initialData);
            }
          }
        })
        .catch(function (error: {
          message?: string;
          response?: { data?: { message?: string } };
        }) {
          if (error?.response?.data?.message) {
            consoleLog(initialUrl, error.response.data.message);
            showError(error.response.data.message);
          } else {
            showError(error.message || 'An error occurred');
          }
          setLoading(false);
        });
    };
    if (allowApiCall && !responsePendingRef.current) fetchData();
    return () => {
      didCancelRef.current = true;
    };
  }, [initialUrl, page, queryParams, allowApiCall, refreshing]);

  return [
    {
      loading,
      apiData,
      page,
      isLoadingMore,
      refreshing,
      initialUrl,
      hasMoreRecord,
    },
    {
      setPage,
      setData,
      setLoading,
      reCallAPI,
      updateInitialUrl,
      setQueryParams,
      setAllowApiCall,
      setLoadingMore,
      setRefreshing,
    },
  ];
};

export const trimObjectValues = <T extends Record<string, unknown>>(
  obj: T,
): T => {
  if (isEmptyObject(obj)) {
    return obj;
  }
  Object.keys(obj).forEach((key) => {
    if (obj[key] && typeof obj[key] === 'string') {
      (obj as Record<string, unknown>)[key] = (obj[key] as string).trim();
    }
  });
  return obj;
};

const handleApiResponse = <T>(
  url: string,
  fetchSuccess: () => void,
  data: AxiosResponse<T>,
  resolve: (data: ApiResponse<T>) => void,
  reject: (data: any) => void,
) => {
  // log(url, data.data);
  fetchSuccess();
  if (isRequestSuccessful(data.status)) {
    return resolve(data.data as ApiResponse<T>);
  } else {
    return reject(data.data);
  }
};

type ChecksumError = {
  message: string;
  originalError: string;
  isChecksumError?: boolean;
  isTimestampError?: boolean;
};

const handleAPIError = (
  url: string,
  fetchSuccess: () => void,
  error: { message?: string; response?: { data?: unknown } },
  reject: (reason: unknown) => void,
): void => {
  fetchSuccess();
  if (error?.message) {
    if (
      error.message.includes('Checksum validation failed') ||
      error.message.includes('data integrity compromised')
    ) {
      const checksumError: ChecksumError = {
        message:
          'Data integrity check failed. Please refresh the page and try again.',
        originalError: error.message,
        isChecksumError: true,
      };
      reject(checksumError);
      return;
    }

    if (
      error.message.includes('timestamp validation failed') ||
      error.message.includes('replay attack')
    ) {
      const timestampError: ChecksumError = {
        message:
          'Request validation failed. Please refresh the page and try again.',
        originalError: error.message,
        isTimestampError: true,
      };
      reject(timestampError);
      return;
    }
  }

  if (error?.response?.data) {
    reject(error.response.data);
  } else {
    reject(error);
  }
};

export const postDataApi = <T>(
  url: string,
  infoViewActionsContext: InfoViewActionsContextType,
  payload: unknown,
  isHideLoader = false,
  headers?: Record<string, string>,
): Promise<ApiResponse<T>> => {
  const {fetchStart, fetchFinish} = infoViewActionsContext;
  return new Promise((resolve, reject) => {
    if (!isHideLoader) fetchStart();

    httpClient
      .post(url, sanitizeData(payload), headers ? {headers} : {})
      .then((data: AxiosResponse<T>) => {
        return handleApiResponse(url, fetchFinish, data, resolve, reject);
      })
      .catch((error) => {
        return handleAPIError(url, fetchFinish, error, reject);
      });
  });
};

export const localPostDataApi = <T = unknown>(
  url: string,
  infoViewActionsContext: InfoViewActionsContextType,
  payload: unknown,
  isHideLoader = false,
  headers?: Record<string, string>,
): Promise<ApiResponse<T>> => {
  const {fetchStart, fetchFinish} = infoViewActionsContext;
  return new Promise((resolve, reject) => {
    if (!isHideLoader) fetchStart();

    httpLocalClient
      .post(url, sanitizeData(payload), headers ? {headers} : {})
      .then((data: AxiosResponse<T>) => {
        return handleApiResponse(url, fetchFinish, data, resolve, reject);
      })
      .catch((error) => {
        return handleAPIError(url, fetchFinish, error, reject);
      });
  });
};

export const putDataApi = <T = unknown>(
  url: string,
  infoViewActionsContext: InfoViewActionsContextType,
  payload: unknown,
  isHideLoader = false,
): Promise<ApiResponse<T>> => {
  const {fetchStart, fetchFinish} = infoViewActionsContext;
  return new Promise((resolve, reject) => {
    if (!isHideLoader) fetchStart();
    httpClient
      .put(url, sanitizeData(payload))
      .then((data: AxiosResponse<T>) => {
        return handleApiResponse(url, fetchFinish, data, resolve, reject);
      })
      .catch((error) => {
        return handleAPIError(url, fetchFinish, error, reject);
      });
  });
};

export const patchDataApi = <T = unknown>(
  url: string,
  infoViewActionsContext: InfoViewActionsContextType,
  payload: unknown,
  isHideLoader = false,
): Promise<ApiResponse<T>> => {
  const {fetchStart, fetchFinish} = infoViewActionsContext;
  return new Promise((resolve, reject) => {
    if (!isHideLoader) fetchStart();
    httpClient
      .patch(url, sanitizeData(payload))
      .then((data: AxiosResponse<T>) => {
        return handleApiResponse(url, fetchFinish, data, resolve, reject);
      })
      .catch((error) => {
        return handleAPIError(url, fetchFinish, error, reject);
      });
  });
};

export const getDataApi = <T = unknown>(
  url: string,
  infoViewActionsContext: InfoViewActionsContextType,
  params: Record<string, unknown> = {},
  isHideLoader = false,
  headers?: Record<string, string>,
  responseType: ResponseType = 'json',
): Promise<ApiResponse<T>> => {
  const {fetchStart, fetchFinish} = infoViewActionsContext;
  return new Promise((resolve, reject) => {
    if (!isHideLoader) fetchStart();
    httpClient
      .get(url, {
        params: sanitizeData(params),
        headers,
        responseType: responseType,
      })
      .then((data: AxiosResponse<T>) => {
        return handleApiResponse(url, fetchFinish, data, resolve, reject);
      })
      .catch((error) => {
        return handleAPIError(url, fetchFinish, error, reject);
      });
  });
};

export const deleteDataApi = <T = unknown>(
  url: string,
  infoViewContext: InfoViewActionsContextType,
  params: Record<string, unknown> = {},
  payload: unknown = {},
  isHideLoader = false,
): Promise<ApiResponse<T>> => {
  const {fetchStart, fetchFinish} = infoViewContext;
  return new Promise((resolve, reject) => {
    if (!isHideLoader) fetchStart();
    httpClient
      .delete(url, {params, data: payload})
      .then((data: AxiosResponse<T>) => {
        if (data.status === 204) {
          resolve({message: 'Deleted Successfully'} as ApiResponse<T>);
        } else {
          handleApiResponse(url, fetchFinish, data, resolve, reject);
        }
      })
      .catch((error) => {
        return handleAPIError(url, fetchFinish, error, reject);
      });
  });
};

export const uploadDataApi = <T = unknown>(
  url: string,
  infoViewContext: InfoViewActionsContextType,
  payload: unknown,
  isHideLoader = false,
  onUploadProgress: (progressEvent: AxiosProgressEvent) => void = (
    progressEvent,
  ) => {
    consoleLog(
      'uploadProgress',
      Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1)),
    );
  },
): Promise<ApiResponse<T>> => {
  const {fetchStart, fetchFinish} = infoViewContext;
  return new Promise((resolve, reject) => {
    if (!isHideLoader) fetchStart();
    httpClient
      .post(url, payload, {
        onUploadProgress,
        headers: {
          'content-type': 'application/x-www-form-urlencoded',
        },
      })
      .then((data: AxiosResponse<T>) => {
        return handleApiResponse(url, fetchFinish, data, resolve, reject);
      })
      .catch((error) => {
        return handleAPIError(url, fetchFinish, error, reject);
      });
  });
};

export const uploadPutDataApi = <T = unknown>(
  url: string,
  infoViewContext: InfoViewActionsContextType,
  payload: unknown,
  isHideLoader = false,
): Promise<ApiResponse<T>> => {
  const {fetchStart, fetchFinish} = infoViewContext;
  return new Promise((resolve, reject) => {
    if (!isHideLoader) fetchStart();
    httpClient
      .put(url, payload, {
        headers: {
          'content-type': 'multipart/form-data',
        },
      })
      .then((data: AxiosResponse<T>) => {
        return handleApiResponse(url, fetchFinish, data, resolve, reject);
      })
      .catch((error) => {
        return handleAPIError(url, fetchFinish, error, reject);
      });
  });
};

export const uploadPostDataApi = <T = unknown>(
  url: string,
  infoViewContext: InfoViewActionsContextType,
  payload: unknown,
  isHideLoader = false,
): Promise<ApiResponse<T>> => {
  const {fetchStart, fetchFinish} = infoViewContext;
  return new Promise((resolve, reject) => {
    if (!isHideLoader) fetchStart();
    httpClient
      .post(url, payload, {
        headers: {
          'content-type': 'multipart/form-data',
        },
      })
      .then((data: AxiosResponse<T>) => {
        return handleApiResponse(url, fetchFinish, data, resolve, reject);
      })
      .catch((error) => {
        return handleAPIError(url, fetchFinish, error, reject);
      });
  });
};

export const downloadDataApi = (
  url: string,
  infoViewContext: InfoViewActionsContextType,
  params: Record<string, unknown> = {},
  isHideLoader = false,
): Promise<ArrayBuffer> => {
  const {fetchStart, fetchFinish} = infoViewContext;
  return new Promise((resolve, reject) => {
    if (!isHideLoader) fetchStart();
    httpClient
      .get(url, {
        params,
        responseType: 'arraybuffer',
        headers: {
          'content-type': 'application/x-www-form-urlencoded',
        },
      })
      .then((res: AxiosResponse<ArrayBuffer>) => {
        fetchFinish();
        if (isRequestSuccessful(res.status)) {
          resolve(res.data);
        } else {
          const data = JSON.parse(
            String.fromCharCode.apply(
              null,
              Array.from(new Uint8Array(res.data)),
            ),
          );
          reject(data);
        }
      })
      .catch((error) => {
        return handleAPIError(url, fetchFinish, error, reject);
      });
  });
};

export type UseDownloadDataResult = {
  downloading: boolean;
  downloadData: (
    params?: Record<string, unknown>,
    newFilename?: string | null,
    requestUrl?: string,
  ) => void;
};

export const useDownloadData = (
  url: string,
  filename: string,
  type = 'text/csv',
  responseType: ResponseType = 'json',
): UseDownloadDataResult => {
  const [downloading, setDownloading] = useState(false);
  const infoViewActionsContext = useInfoViewActionsContext();

  const downloadData = useCallback(
    (
      params: Record<string, unknown> = {},
      newFilename: string | null = null,
      requestUrl: string = url,
    ) => {
      setDownloading(true);
      getDataApi<BlobPart>(
        requestUrl,
        infoViewActionsContext,
        params,
        true,
        {},
        responseType,
      )
        .then((data) => {
          if (data) {
            const blob = new Blob([data.data as BlobPart], {
              type: `${type};charset=utf-8;`,
            });
            const blobUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.setAttribute('download', newFilename || filename);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          }
          setDownloading(false);
        })
        .catch((error: { message?: string }) => {
          setDownloading(false);
          infoViewActionsContext.showError(error?.message || 'Download failed');
          console.error('Error on downloading data', error);
        });
    },
    [url, filename, type, responseType, infoViewActionsContext],
  );

  return {
    downloading,
    downloadData,
  };
};
