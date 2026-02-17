'use client';
import { Button, DatePicker, Input, Select, Space } from 'antd';
import { FilterOutlined, SearchOutlined } from '@ant-design/icons';
import {
  Dispatch,
  ReactNode,
  SetStateAction,
  useEffect,
  useState,
} from 'react';
import { isEmptyObject } from './GlobalHelper';
import { getFormattedDate } from './DateHelper';
import { tablePageSize } from '@unpod/constants';
import dayjs, { Dayjs } from 'dayjs';
import { FormatMessageFn } from './LocalizationFormatHelper';

export type FilterSortValue = {
  sortedInfo: SortedInfo;
  filteredInfo: FilteredInfo;
};

export type SortedInfo = {
  field?: string;
  order?: string;
};

export type FilteredInfo = {
  [key: string]: unknown[] | null;
};

export type ExtraInfo = {
  function: (value: unknown, ...args: unknown[]) => unknown;
  filterKey: string;
  otherArgs: unknown[];
};

export type UseTablePaginationProps = {
  initialFilterData?: Record<string, unknown>;
  otherParams?: Record<string, unknown>;
  dependencies?: unknown[];
  setQueryParams: (params: Record<string, unknown>) => void;
  setSummaryQueryParams?: (params: Record<string, unknown>) => void;
  extraInfo?: ExtraInfo;
  dependentCallback?: (
    filterData: Record<string, unknown>,
    filterSortValue: FilterSortValue,
  ) => Record<string, unknown>;
};

export type TablePaginationState = {
  currentPage: number;
  pageSize: number;
  filterData: Record<string, unknown>;
  filterInfo: Record<string, unknown>;
};

export type TablePaginationActions = {
  setCurrentPage: Dispatch<SetStateAction<number>>;
  onPageChange: (page: number, pageSize: number) => void;
  setFilterData: (data: Record<string, unknown>) => void;
  onShowSizeChange: (current: number, size: number) => void;
  onTableFilterChange: (
    pagination: unknown,
    filters: FilteredInfo,
    sorter: SortedInfo,
  ) => void;
};

export const useTablePagination = ({
  initialFilterData = {},
  otherParams = {},
  dependencies = [],
  setQueryParams,
  setSummaryQueryParams,
  extraInfo,
  dependentCallback,
}: UseTablePaginationProps): [TablePaginationState, TablePaginationActions] => {
  const [pageSize, setPageSize] = useState(tablePageSize);
  const [currentPage, setCurrentPage] = useState(1);

  const [filterData, updateFilterData] = useState(initialFilterData);
  const [filterSortValue, updateFilterSortValue] = useState<FilterSortValue>({
    sortedInfo: {},
    filteredInfo: {},
  });

  const setFilterData = (data: Record<string, unknown>) => {
    updateFilterData({ ...filterData, ...data });
  };

  useEffect(() => {
    if (dependencies.length > 0) {
      setCurrentPage(1);
      if (
        !(
          isEmptyObject(
            filterSortValue.sortedInfo as Record<string, unknown>,
          ) &&
          isEmptyObject(filterSortValue.filteredInfo as Record<string, unknown>)
        )
      ) {
        updateFilterSortValue({
          sortedInfo: {},
          filteredInfo: {},
        });
      }
    }
  }, dependencies);

  const getExtraParams = (): Record<string, unknown> => {
    if (extraInfo && extraInfo.function) {
      return {
        [extraInfo.filterKey]: extraInfo.function(
          filterData?.[extraInfo.filterKey],
          ...extraInfo.otherArgs,
        ),
      };
    }
    return {};
  };

  useEffect(() => {
    if (
      currentPage === 1 &&
      !isEmptyObject(filterData as Record<string, unknown>)
    ) {
      setQueryParams({
        page: currentPage,
        page_size: pageSize,
        ...otherParams,
        ...filterData,
        ...getExtraParams(),
        ...dependentCallback?.(filterData, filterSortValue),
        ...getTableFilterData(filterSortValue),
      });
      if (setSummaryQueryParams) {
        setSummaryQueryParams({
          page: currentPage,
          page_size: pageSize,
          ...otherParams,
          ...filterData,
          ...getExtraParams(),
          ...dependentCallback?.(filterData, filterSortValue),
          ...getTableFilterData(filterSortValue),
        });
      }
    } else if (currentPage !== 1) {
      setCurrentPage(1);
    }
  }, [filterData]);

  useEffect(() => {
    setQueryParams({
      page: currentPage,
      page_size: pageSize,
      ...otherParams,
      ...filterData,
      ...getExtraParams(),
      ...dependentCallback?.(filterData, filterSortValue),
      ...getTableFilterData(filterSortValue),
    });
    if (setSummaryQueryParams) {
      setSummaryQueryParams({
        page: currentPage,
        page_size: pageSize,
        ...otherParams,
        ...filterData,
        ...getExtraParams(),
        ...dependentCallback?.(filterData, filterSortValue),
        ...getTableFilterData(filterSortValue),
      });
    }
  }, [pageSize, currentPage, filterSortValue, ...dependencies]);

  const onPageChange = (page: number, pageSize: number) => {
    setCurrentPage(page);
    setPageSize(pageSize);
  };

  const onShowSizeChange = (current: number, size: number) => {
    setPageSize(size);
  };

  const onTableFilterChange = (
    pagination: unknown,
    filters: FilteredInfo,
    sorter: SortedInfo,
  ) => {
    if (
      sorter.field !== filterSortValue?.sortedInfo?.field ||
      sorter.order !== filterSortValue?.sortedInfo?.order
    ) {
      setCurrentPage(1);
    }
    updateFilterSortValue({
      sortedInfo: sorter,
      filteredInfo: filters,
    });
  };

  return [
    {
      currentPage,
      pageSize,
      filterData,
      filterInfo: getTableFilterData(filterSortValue),
    },
    {
      setCurrentPage,
      onPageChange,
      setFilterData,
      onShowSizeChange,
      onTableFilterChange,
    },
  ];
};

export const getSortColumnData = (
  data: SortedInfo,
): Record<string, string | undefined> => {
  if (data.field) return { [data.field]: data.order };
  return {};
};

const getDate = (date: [Dayjs, Dayjs]): [string, string] => {
  return [
    getFormattedDate(date[0]?.toISOString(), 'YYYY-MM-DD') + 'T00:00:00.240Z',
    getFormattedDate(date[1]?.toISOString(), 'YYYY-MM-DD') + 'T23:59:59.240Z',
  ];
};

export const getFilterData = (data: FilteredInfo): Record<string, unknown> => {
  let filters: Record<string, unknown> = {};
  Object.keys(data).filter((key) => {
    if (data[key]) {
      const value = data[key] as unknown[];
      filters = {
        ...filters,
        [key]: value.length > 1 ? getDate(value as [Dayjs, Dayjs]) : value[0],
      };
    }
    return false;
  });
  return filters;
};

export const getTableFilterData = (
  data: FilterSortValue,
): Record<string, unknown> => {
  return {
    sort: JSON.stringify(getSortColumnData(data.sortedInfo)),
    ...getFilterData(data.filteredInfo),
  };
};

export type TablePaginationConfig = {
  pageSize: number;
  current: number;
  total: number;
  onShowSizeChange?: (current: number, size: number) => void;
  onChange?: (page: number, pageSize: number) => void;
  showSizeChanger: boolean;
  position: string[];
  showTotal: (total: number) => string;
  pageSizeOptions: string[];
};

export const getTablePagination = (
  pageSize = tablePageSize,
  currentPage = 1,
  dataCount = 0,
  onShowSizeChange?: (current: number, size: number) => void,
  onPageChange?: (page: number, pageSize: number) => void,
  customPageSizeOptions?: string[],
): TablePaginationConfig => {
  return {
    pageSize: pageSize,
    current: currentPage,
    total: dataCount,
    onShowSizeChange: onShowSizeChange,
    onChange: onPageChange,
    showSizeChanger: true,
    position: ['bottomCenter'],
    showTotal: (total: number) => `Total ${total} items`,
    pageSizeOptions: customPageSizeOptions || ['5', '10', '20', '50', '100'],
  };
};

export const onSortOrder = <T extends Record<string, unknown>>(
  a: T,
  b: T,
  key: string,
  type: 'numeric' | 'array' | 'string' = 'numeric',
  index = 0,
): number => {
  if (type === 'numeric')
    return (
      (typeof a?.[key] === 'number' ? (a?.[key] as number) : 0) -
      (typeof b?.[key] === 'number' ? (b?.[key] as number) : 0)
    );
  else if (type === 'array')
    return (
      ((a?.[key] as number[])?.[index] || 0) -
      ((b?.[key] as number[])?.[index] || 0)
    );
  else if (type === 'string')
    return (a?.[key] as string)?.localeCompare(b?.[key] as string);
  else return ((a[key] as number) || 0) - ((b[key] as number) || 0);
};

export type FilterDropdownProps = {
  setSelectedKeys: (keys: unknown[]) => void;
  selectedKeys: unknown[];
  confirm: () => void;
  clearFilters?: () => void;
};

export type ColumnSearchProps = {
  filterDropdown: (props: FilterDropdownProps) => ReactNode;
  filterIcon: (filtered: boolean) => ReactNode;
  render: (text: string) => string;
};

export const getColumnSearchProps = (
  title: string,
  dataIndex: string,
  formatMessage: FormatMessageFn,
): ColumnSearchProps => {
  return {
    filterDropdown: ({
      setSelectedKeys,
      selectedKeys,
      confirm,
      clearFilters = () => void 0,
    }: FilterDropdownProps) => (
      <div style={{ padding: 8 }}>
        <Input
          placeholder={`Search ${title}`}
          value={selectedKeys[0] as string}
          onChange={(e) =>
            setSelectedKeys(e.target.value ? [e.target.value] : [])
          }
          onPressEnter={() => handleSearch(selectedKeys, confirm)}
          style={{ marginBottom: 8, display: 'block' }}
        />
        <Space>
          <Button
            type="primary"
            onClick={() => handleSearch(selectedKeys, confirm)}
            icon={<SearchOutlined />}
            size="small"
          >
            {formatMessage({ id: 'common.search' })}
          </Button>
          <Button
            onClick={() => handleReset(clearFilters, confirm)}
            size="small"
          >
            {formatMessage({ id: 'common.reset' })}
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered: boolean) => (
      <FilterOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
    ),
    render: (text: string) => text,
  };
};

export type SelectOption = {
  id: string;
  name: string;
};

export const getColumnSelectBoxProps = (
  title: string,
  dataIndex: string,
  options: SelectOption[] | undefined,
  formatMessage: FormatMessageFn,
): ColumnSearchProps => {
  return {
    filterDropdown: ({
      setSelectedKeys,
      selectedKeys,
      confirm,
      clearFilters = () => void 0,
    }: FilterDropdownProps) => (
      <div style={{ padding: 8 }}>
        <Select
          placeholder={`Search ${title}`}
          value={selectedKeys[0] as string}
          onChange={(newValue: string) =>
            setSelectedKeys(newValue ? [newValue] : [])
          }
          style={{ marginBottom: 8, display: 'block' }}
        >
          {options?.map((unit) => (
            <Select.Option key={unit.id} value={unit.id}>
              {unit.name}
            </Select.Option>
          ))}
        </Select>
        <Space>
          <Button
            type="primary"
            onClick={() => handleSearch(selectedKeys, confirm)}
            icon={<SearchOutlined />}
            size="small"
          >
            {formatMessage({ id: 'common.search' })}
          </Button>
          <Button
            onClick={() => handleReset(clearFilters, confirm)}
            size="small"
          >
            {formatMessage({ id: 'common.reset' })}
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered: boolean) => (
      <FilterOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
    ),
    render: (text: string) => text,
  };
};

export const getColumnDateProps = (
  title: string,
  dataIndex: string,
  formatMessage: FormatMessageFn,
): ColumnSearchProps => {
  return {
    filterDropdown: ({
      setSelectedKeys,
      selectedKeys,
      confirm,
      clearFilters = () => void 0,
    }: FilterDropdownProps) => (
      <div style={{ padding: 8 }}>
        <DatePicker.RangePicker
          placeholder={[
            formatMessage({ id: 'common.startTime' }),
            formatMessage({ id: 'common.endTime' }),
          ]}
          picker="date"
          format="DD-MM-YYYY"
          value={selectedKeys as [Dayjs | null, Dayjs | null]}
          onChange={(data) => {
            setSelectedKeys(data as unknown[]);
          }}
          onOk={() => {
            handleSearch(selectedKeys, confirm);
          }}
          style={{ marginRight: 8 }}
        />
        <Space>
          <Button
            type="primary"
            onClick={() => handleSearch(selectedKeys, confirm)}
            icon={<SearchOutlined />}
            size="small"
          >
            {formatMessage({ id: 'common.search' })}
          </Button>
          <Button
            onClick={() => handleReset(clearFilters, confirm)}
            size="small"
          >
            {formatMessage({ id: 'common.reset' })}
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered: boolean) => (
      <FilterOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
    ),
    render: (text: string) => text,
  };
};

export const getColumnDateTimeProps = (
  title: string,
  dataIndex: string,
  formatMessage: FormatMessageFn,
): ColumnSearchProps => {
  return {
    filterDropdown: ({
      setSelectedKeys,
      selectedKeys,
      confirm,
      clearFilters = () => void 0,
    }: FilterDropdownProps) => (
      <div style={{ padding: 8 }}>
        <DatePicker
          placeholder={title}
          format="DD-MM-YYYY HH:mm:ss A"
          value={
            selectedKeys?.length > 0
              ? dayjs(selectedKeys[0] as string, 'DD-MM-YYYY HH:mm:ss')
              : null
          }
          onChange={(data) => {
            if (data) {
              setSelectedKeys([dayjs(data).format('DD-MM-YYYY HH:mm:ss')]);
            } else {
              setSelectedKeys([]);
            }
          }}
          style={{ marginRight: 8 }}
        />
        <Space>
          <Button
            type="primary"
            onClick={() => {
              handleSearch(selectedKeys, confirm);
            }}
            icon={<SearchOutlined />}
            size="small"
          >
            {formatMessage({ id: 'common.search' })}
          </Button>
          <Button
            onClick={() => handleReset(clearFilters, confirm)}
            size="small"
          >
            {formatMessage({ id: 'common.reset' })}
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered: boolean) => (
      <FilterOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
    ),
    render: (text: string) => text,
  };
};

export const getColumnReturnPeriodProps = (
  title: string,
  dataIndex: string,
  formatMessage: FormatMessageFn,
): ColumnSearchProps => {
  return {
    filterDropdown: ({
      setSelectedKeys,
      selectedKeys,
      confirm,
      clearFilters = () => void 0,
    }: FilterDropdownProps) => (
      <div style={{ padding: 8 }}>
        <DatePicker.RangePicker
          placeholder={['Start date', 'End date']}
          value={selectedKeys as [Dayjs | null, Dayjs | null]}
          picker="month"
          onChange={(data) => {
            setSelectedKeys(data as unknown[]);
          }}
          onOk={() => {
            handleSearch(selectedKeys, confirm);
          }}
          style={{ marginBottom: 8 }}
        />
        <Space>
          <Button
            type="primary"
            onClick={() => handleSearch(selectedKeys, confirm)}
            icon={<SearchOutlined />}
            size="small"
          >
            {formatMessage({ id: 'common.search' })}
          </Button>
          <Button
            onClick={() => handleReset(clearFilters, confirm)}
            size="small"
          >
            {formatMessage({ id: 'common.reset' })}
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered: boolean) => (
      <FilterOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
    ),
    render: (text: string) => text,
  };
};

const handleSearch = (selectedKeys: unknown[], confirm: () => void): void => {
  confirm();
};

export type ColumnConfig = {
  align: string;
  fixed?: string;
};

export const getActionColumn = (): ColumnConfig => {
  return { align: 'center', fixed: 'right' };
};

export const getFirstColumn = (): ColumnConfig => {
  return { align: 'left' };
};

export const getAmountColumn = (): ColumnConfig => {
  return { align: 'right' };
};

export const getNumberColumn = (): ColumnConfig => {
  return { align: 'right' };
};

export const getSpecialColumn = (): ColumnConfig => {
  return { align: 'center' };
};

export const getDateColumn = (): ColumnConfig => {
  return { align: 'right' };
};

const handleReset = (clearFilters: () => void, confirm: () => void): void => {
  clearFilters();
  confirm();
};
