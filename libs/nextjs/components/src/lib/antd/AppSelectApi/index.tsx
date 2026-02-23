import {useEffect, useState} from 'react';
import {useGetDataApi} from '@unpod/providers';
import AppSelect from '../AppSelect';
import type {SelectProps} from 'antd/es/select';

type SelectOption = { value: string | number; label: string };

type AppSelectApiProps<T> = Omit<SelectProps, 'options'> & {
  apiEndpoint: string;
  params?: Record<string, unknown>;
  initialFetch?: boolean;
  transform?: (data: T) => SelectOption | null;
};

const isSelectOption = (data: unknown): data is SelectOption => {
  if (!data || typeof data !== 'object') return false;
  const candidate = data as Record<string, unknown>;
  return (
    (typeof candidate.value === 'string' ||
      typeof candidate.value === 'number') &&
    typeof candidate.label === 'string'
  );
};

const AppSelectApi = <T, >({
                             apiEndpoint,
                             params = {},
                             initialFetch = true,
                             transform = (data: T) => (isSelectOption(data) ? data : null),
                             ...restProps
                           }: AppSelectApiProps<T>) => {
  const [options, setOptions] = useState<SelectOption[]>([]);
  const [{loading, apiData}, {setQueryParams}] = useGetDataApi<T[]>(
    apiEndpoint,
    {data: []},
    params,
    initialFetch,
  );

  console.log('Api data response', apiData?.data);

  useEffect(() => {
    if (initialFetch === false) {
      setQueryParams(params);
    }
  }, [initialFetch, params, setQueryParams]);

  useEffect(() => {
    if (apiData?.data) {
      const nextOptions = (apiData.data ?? [])
        .map((item: T) => transform(item))
        .filter((item): item is SelectOption => !!item);
      setOptions(nextOptions);
    }
  }, [apiData, transform]);

  return <AppSelect loading={loading} options={options} {...restProps} />;
};

export default AppSelectApi;
