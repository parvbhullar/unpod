import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  AppTableProps,
  CellKeyboardEvent,
  CellKeyDownArgs,
  FilterType,
  SortColumn,
  themeOptions,
} from './core/models/data-grid';
import { Empty, type TablePaginationConfig } from 'antd';
import { ThemeProvider } from 'styled-components';
import { PAGINATION_SIZE, tablePageSize } from './core/constants/AppConst';
import AppDraggableDataGrid from './AppDraggableDataGrid';
import LoadingView from './core/components/LoadingView';
import TablePagination from './core/TablePagination';
import DataGrid, { SelectColumn } from './core';
import { StyledTableEmptyWrapper, StyledTableWrapper } from './index.styled';
import LoadingMoreView from './core/components/LoadingMoreView';

function rowKeyGetter(row: any, rowKey: string) {
  return row?.[rowKey];
}

const sizeMap: Record<string, number> = {
  small: 39,
  middle: 47,
  large: 55,
};

function keysToSet(keys: React.Key[]): ReadonlySet<React.Key> {
  const numbers = keys.map((key) => key);
  return new Set(numbers);
}
const OFFSET_MARGIN = 74;

const EMPTY_STATE_SIZE = 136;

function paginateArray(data: any[], pagination: TablePaginationConfig) {
  const { pageSize, current } = pagination;

  if (pageSize && current) {
    const startIndex = (current - 1) * pageSize;
    const endIndex = startIndex + pageSize;

    // Slice the data array to get the data for the current page
    return data.slice(startIndex, endIndex);
  }
  return [];
}

function isAtBottom({ currentTarget }: React.UIEvent<HTMLDivElement>): boolean {
  return (
    currentTarget.scrollTop + 10 >=
    currentTarget.scrollHeight - currentTarget.clientHeight
  );
}

const defaultThemeOptions: themeOptions = {
  font: {
    size: {
      base: '14px',
      lg: '16px',
      sm: '12px',
      xl: '18px',
    },
    weight: {
      light: 300,
      regular: 400,
      medium: 500,
      semiBold: 600,
      bold: 700,
    },
  },
  text: {
    heading: 'rgba(0, 0, 0, 0.88)',
    primary: '#595959',
    secondary: '#8D8C8C',
    disabled: '#8D8C8C',
    placeholder: '#8D8C8C',
    hint: '#bcbaba',
  },
  border: {
    color: '#245a94',
    width: '1px',
    radius: '10px',
  },
  table: {
    textColor: 'rgba(0, 0, 0, 0.88)',
    outlineColor: '#66afe9',
    borderColor: '#f0f0f0',
    borderHoverColor: '#f0f0f0',
    activeBorderColor: '#66afe9',
    selectedHoverColor: '#99a3ba',
    headerBgColor: '#fafafa',
    rowOverBgColor: '#ececec',
    headerIconColor: 'rgba(0, 0, 0, 0.29)',
  },
  primaryColor: '#182a88',
  backgroundColor: '#ffffff',
  copiedBgColor: '#ccccff',
  errorColor: '#cf2a27',
  breakpoints: {
    xs: 480,
    sm: 576,
    md: 768,
    lg: 992,
    xl: 1200,
    xxl: 1600,
  },
  direction: 'ltr',
};

const AppDataGrid = ({
  columns,
  dataSource = [],
  loading,
  isLoadingMore,
  id,
  onChange,
  rowKey = 'id',
  className,
  rowSelection,
  pagination,
  isDraggable = false,
  size = 'small',
  bordered = false,
  onRowDragEnd,
  customRowHeight,
  defaultColumnOptions,
  extraHeight = 0,
  customBlockSize,
  fullHeight,
  hasLocalFilters = false,
  themeOptions,
  onScrolledToBottom,
  ...restProps
}: AppTableProps) => {
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const [localPaginated, setLocalPaginated] = useState<boolean>(false);
  const [rows, setRows] = useState<any[]>([]);
  const [sortColumns, setSortColumns] = useState<readonly SortColumn[]>([]);
  const [filters, setFilter] = useState<FilterType>({});
  const [selectedRows, setSelectedRows] = useState(
    (): ReadonlySet<React.Key> => new Set(),
  );

  const gridTheme = useMemo(
    () => ({
      ...defaultThemeOptions,
      ...themeOptions,
    }),
    [themeOptions],
  );

  const { hasChildren, extraRowSpanCount } = useMemo(() => {
    const hasChildren = columns?.find((item) => item?.children);
    const extraRowSpanCount = dataSource?.reduce(
      (acc, val) =>
        acc + (val?.row_span && val?.row_span > 2 ? val?.row_span - 2 : 0),
      0,
    );
    return {
      hasChildren,
      extraRowSpanCount,
    };
  }, [columns, dataSource]);

  const { blockSize } = useMemo(() => {
    const rowHeight =
      customRowHeight && typeof customRowHeight === 'number'
        ? customRowHeight
        : sizeMap[size];

    const headerRowHeight = sizeMap[size];

    const paginationHeight = pagination ? PAGINATION_SIZE : 0;

    const totalHeaderRowsHeight = hasChildren
      ? 2 * headerRowHeight
      : headerRowHeight;

    let totalRows;

    if (localPaginated) {
      totalRows =
        (rows?.length > tablePageSize ? tablePageSize : rows.length) +
        extraRowSpanCount;
    } else {
      totalRows =
        (dataSource?.length > tablePageSize
          ? tablePageSize
          : dataSource.length) + extraRowSpanCount;
    }

    let bodyHeight = 0;

    bodyHeight = rowHeight * totalRows;

    const blockSize =
      customBlockSize ||
      totalHeaderRowsHeight + bodyHeight + paginationHeight + 20;
    const minHeight = totalHeaderRowsHeight + EMPTY_STATE_SIZE + 100;

    return {
      blockSize,
      minHeight,
    };
  }, [
    hasChildren,
    customBlockSize,
    extraRowSpanCount,
    dataSource?.length,
    rows,
    localPaginated,
    pagination,
    size,
    customRowHeight,
  ]);
  useEffect(() => {
    if (dataSource) {
      const pageSize = (
        pagination as { pageSize: TablePaginationConfig['pageSize'] }
      )?.pageSize;
      if (pageSize && pageSize < dataSource?.length) {
        setLocalPaginated(true);
        setRows(paginateArray(dataSource, pagination as TablePaginationConfig));
      } else {
        setLocalPaginated(false);
        setRows(dataSource);
      }
    }
  }, [dataSource, pagination]);

  useEffect(() => {
    if (rowSelection?.selectedRowKeys) {
      setSelectedRows(keysToSet(rowSelection.selectedRowKeys));
    }
  }, [rowSelection?.selectedRowKeys]);

  useEffect(() => {
    if (columns?.length && onChange) {
      if (sortColumns?.length === 0) {
        onChange(pagination, filters, {});
      } else {
        const sorterColumn = columns?.find(
          (item) => item.dataIndex === sortColumns[0].columnKey,
        );
        const sorter = {
          column: sorterColumn,
          order: sortColumns[0].direction === 'ASC' ? 'ascend' : 'descend',
          field: sortColumns[0].columnKey,
          columnKey: sortColumns[0].columnKey,
        };
        onChange(pagination, filters, sorter);
      }
    }
  }, [filters, sortColumns]);

  const sortedRows = useMemo(() => {
    if (sortColumns.length === 0) return rows;

    return [...rows].sort((a, b) => {
      for (const sort of sortColumns) {
        const sortingColumn = columns.find(
          (item) => item.key === sort.columnKey,
        );
        if (sortingColumn?.sorter) {
          const compResult = sortingColumn.sorter(
            a,
            b,
            sort.columnKey,
            typeof a[sort.columnKey],
          );

          if (compResult !== 0) {
            return sort.direction === 'ASC' ? compResult : -compResult;
          }
        }
      }
      return 0;
    });
  }, [rows, sortColumns, columns]);

  if (rowSelection?.onChange) {
    columns = [SelectColumn, ...columns];
  }

  function onSetSelectedRows(keys: Set<React.Key>) {
    setSelectedRows(keys);
    if (rowKey) {
      const selectedRows = rows?.filter((item) => keys.has(item?.[rowKey]));

      if (rowSelection?.onChange) {
        rowSelection?.onChange([...keys], selectedRows || []);
      }
    }
  }

  function handleCellKeyDown(
    args: CellKeyDownArgs<any>,
    event: CellKeyboardEvent,
  ) {
    event.preventGridDefault();
  }

  const handleScroll = (event: React.UIEvent<HTMLDivElement>) => {
    if (loading || isLoadingMore || !isAtBottom(event)) return;

    onScrolledToBottom?.();
  };

  return (
    <ThemeProvider theme={gridTheme as any}>
      <StyledTableWrapper
        className={`main-table ${className ?? ''}`}
        style={{
          opacity: loading ? 0.5 : 1,
          // blockSize: dataSource?.length && !fullHeight ? blockSize : 'auto',
          blockSize: fullHeight
            ? undefined
            : `calc(100vh - ${OFFSET_MARGIN + extraHeight}px)`,
          maxBlockSize: fullHeight
            ? undefined
            : `calc(100vh - ${OFFSET_MARGIN + extraHeight}px)`,
        }}
        ref={wrapperRef}
      >
        {isDraggable ? (
          <AppDraggableDataGrid
            id={id}
            rowKey={rowKey}
            dataSource={dataSource}
            wrapperRef={wrapperRef}
            blockSize={blockSize}
            onRowDragEnd={onRowDragEnd}
            setSortColumns={(value) => {
              setSortColumns(value);
            }}
            handleCellKeyDown={handleCellKeyDown}
            setFilter={setFilter}
            sortedRows={sortedRows}
            loading={loading}
            rowSelection={rowSelection}
            rowKeyGetter={rowKeyGetter}
            columns={columns || []}
            pagination={pagination}
            rowHeight={sizeMap[size]}
            selectedRows={selectedRows}
            onSetSelectedRows={onSetSelectedRows}
            defaultColumnOptions={defaultColumnOptions}
            sortColumns={sortColumns}
            filters={filters}
            bordered={bordered}
            hidePagination
            onScroll={handleScroll}
            {...restProps}
          />
        ) : (
          <React.Fragment>
            {dataSource?.length || hasLocalFilters ? (
              <>
                <DataGrid
                  id={id}
                  className="fill-grid"
                  rowKey={rowKey || 'id'}
                  rowSelectionType={rowSelection?.type ?? 'checkbox'}
                  rowKeyGetter={rowKeyGetter}
                  columns={columns || []}
                  defaultColumnOptions={{
                    resizable: true,
                    ...defaultColumnOptions,
                  }}
                  rowHeight={customRowHeight || sizeMap[size]}
                  headerRowHeight={sizeMap[size]}
                  rows={
                    dataSource?.length !== sortedRows?.length
                      ? localPaginated
                        ? sortedRows
                        : dataSource || []
                      : sortedRows || []
                  }
                  selectedRows={selectedRows}
                  onSelectedRowsChange={onSetSelectedRows}
                  onRowsChange={setRows}
                  sortColumns={sortColumns}
                  onSortColumnsChange={setSortColumns}
                  filters={filters}
                  onFiltersChange={setFilter}
                  direction="ltr"
                  border={bordered}
                  // onCellKeyDown={handleCellKeyDown}
                  hidePagination={!pagination}
                  onScroll={handleScroll}
                  style={{
                    blockSize:
                      pagination && !fullHeight
                        ? `calc(100% - ${PAGINATION_SIZE}px)`
                        : '100%',
                  }}
                  {...restProps}
                />
                {pagination && <TablePagination {...pagination} />}
              </>
            ) : (
              <DataGrid
                id="__id"
                rowKey="__id"
                className="fill-grid"
                rowSelectionType={rowSelection?.type ?? 'checkbox'}
                rowKeyGetter={rowKeyGetter}
                columns={columns || []}
                defaultColumnOptions={{
                  resizable: true,
                  ...defaultColumnOptions,
                }}
                rowHeight={customRowHeight || sizeMap[size]}
                headerRowHeight={sizeMap[size]}
                rows={[]}
                selectedRows={selectedRows}
                onSelectedRowsChange={onSetSelectedRows}
                onRowsChange={setRows}
                sortColumns={sortColumns}
                onSortColumnsChange={setSortColumns}
                filters={filters}
                onFiltersChange={setFilter}
                direction="ltr"
                border={bordered}
                renderers={{
                  noRowsFallback: (
                    <StyledTableEmptyWrapper
                      style={{
                        maxWidth: wrapperRef?.current?.clientWidth || '100%',
                      }}
                    >
                      <Empty
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        description="No data found!"
                      />
                    </StyledTableEmptyWrapper>
                  ),
                }}
                hidePagination
                {...restProps}
              />
            )}

            {loading ? (
              <LoadingView
                position="absolute"
                style={{ backgroundColor: 'transparent' }}
              />
            ) : null}
          </React.Fragment>
        )}

        {isLoadingMore ? <LoadingMoreView /> : null}
      </StyledTableWrapper>
    </ThemeProvider>
  );
};

export default AppDataGrid;
