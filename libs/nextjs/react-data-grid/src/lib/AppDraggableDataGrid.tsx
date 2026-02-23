import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {Empty} from 'antd';
import type {
  AppTableProps,
  CellKeyboardEvent,
  CellKeyDownArgs,
  FilterType,
  Maybe,
  RenderHeaderCellProps,
  RenderRowProps,
  SortColumn,
} from './core/models/data-grid';

import {DndProvider} from 'react-dnd';
import {HTML5Backend} from 'react-dnd-html5-backend';
import {PAGINATION_SIZE} from './core/constants/AppConst';
import {DraggableHeaderRenderer, DraggableRowRenderer,} from './core/components';
import DataGrid from './core/DataGrid';
import TablePagination from './core/TablePagination';
import LoadingView from './core/components/LoadingView';
import {StyledTableEmptyWrapper} from './index.styled';

type DraggableTableProps = AppTableProps & {
  sortedRows: any[];
  blockSize: number;
  wrapperRef: React.RefObject<HTMLDivElement | null>;
  rowHeight: number;
  filters: FilterType;
  sortColumns: readonly SortColumn[];
  selectedRows: ReadonlySet<React.Key>;
  setSortColumns: React.Dispatch<React.SetStateAction<readonly SortColumn[]>>;
  rowKeyGetter: Maybe<(row: any, rowKey: string) => number>;
  setFilter: React.Dispatch<React.SetStateAction<FilterType>>;

  handleCellKeyDown(args: CellKeyDownArgs<any>, event: CellKeyboardEvent): void;
};

const AppDraggableDataGrid = <R, SR>({
                                       columns,
                                       sortedRows,
                                       dataSource,
                                       loading,
                                       id,
                                       onChange,
                                       rowKey,
                                       rowSelection,
                                       pagination,
                                       blockSize,
                                       wrapperRef,
                                       rowHeight,
                                       filters,
                                       customGridTempleteRows,
                                       sortColumns,
                                       selectedRows,
                                       size = 'large',
                                       bordered = false,
                                       onRowDragEnd,
                                       rowKeyGetter,
                                       setSortColumns,
                                       setFilter,
                                       onSetSelectedRows,
                                       handleCellKeyDown,
                                       ...restProps
                                     }: DraggableTableProps) => {
  const [updatedColumns, setUpdatedColumns] = useState(columns || []);
  const [updatedRows, setUpdatedRows] = useState<any[]>([]);

  useEffect(() => {
    if (sortedRows) {
      setUpdatedRows(sortedRows);
    }
  }, [sortedRows]);

  useEffect(() => {
    if (columns) {
      setUpdatedColumns(columns);
    }
  }, [columns]);

  const draggableColumns = useMemo(() => {
    function renderHeaderCell(props: RenderHeaderCellProps<R>) {
      return (
        <DraggableHeaderRenderer
          {...props}
          onColumnsReorder={handleColumnsReorder}
        />
      );
    }

    function handleColumnsReorder(sourceKey: string, targetKey: string) {
      const sourceColumnIndex = updatedColumns.findIndex(
        (c) => c.dataIndex === sourceKey,
      );
      const targetColumnIndex = updatedColumns.findIndex(
        (c) => c.dataIndex === targetKey,
      );
      const reorderedColumns = [...updatedColumns];

      reorderedColumns.splice(
        targetColumnIndex,
        0,
        reorderedColumns.splice(sourceColumnIndex, 1)[0],
      );

      setUpdatedColumns(reorderedColumns);
    }

    return updatedColumns.map((c) => {
      if (c.dataIndex === 'id') return c;
      return {...c, renderHeaderCell};
    });
  }, [updatedColumns]);

  const renderRow = useCallback((key: React.Key, props: RenderRowProps<R>) => {
    function onRowReorder(fromIndex: number, toIndex: number) {
      setUpdatedRows((rows) => {
        const newRows = [...rows];
        newRows.splice(toIndex, 0, newRows.splice(fromIndex, 1)[0]);
        if (onRowDragEnd) onRowDragEnd(newRows);
        return newRows;
      });
    }

    return (
      <DraggableRowRenderer key={key} {...props} onRowReorder={onRowReorder}/>
    );
  }, []);

  return (
    <React.Fragment>
      {dataSource?.length && !loading ? (
        <>
          <DndProvider backend={HTML5Backend}>
            <DataGrid
              id={id}
              className="fill-grid"
              rowKey={rowKey || 'id'}
              rowSelectionType={rowSelection?.type ?? 'checkbox'}
              rowKeyGetter={rowKeyGetter}
              columns={draggableColumns}
              defaultColumnOptions={{
                resizable: true,
              }}
              rowHeight={rowHeight}
              customGridTemplateRows={customGridTempleteRows}
              rows={updatedRows}
              selectedRows={selectedRows}
              onSelectedRowsChange={onSetSelectedRows}
              onRowsChange={setUpdatedRows}
              sortColumns={sortColumns}
              onSortColumnsChange={setSortColumns}
              filters={filters}
              onFiltersChange={setFilter}
              direction="ltr"
              border={bordered}
              onCellKeyDown={handleCellKeyDown}
              style={{
                blockSize: pagination
                  ? `calc(100% - ${PAGINATION_SIZE}px)`
                  : '100%',
              }}
              renderers={{
                renderRow,
              }}
              {...restProps}
            />
          </DndProvider>
          {pagination && <TablePagination {...pagination} />}
        </>
      ) : null}

      {(dataSource?.length === 0 || loading) && (
        <DndProvider backend={HTML5Backend}>
          <DataGrid
            id="__id"
            rowKey="__id"
            className="fill-grid"
            rowSelectionType={rowSelection?.type ?? 'checkbox'}
            rowKeyGetter={rowKeyGetter}
            columns={draggableColumns || []}
            defaultColumnOptions={{
              resizable: true,
            }}
            rowHeight={rowHeight}
            customGridTemplateRows={customGridTempleteRows}
            rows={[]}
            selectedRows={selectedRows}
            onSelectedRowsChange={onSetSelectedRows}
            onRowsChange={setUpdatedRows}
            sortColumns={sortColumns}
            onSortColumnsChange={setSortColumns}
            filters={filters}
            onFiltersChange={setFilter}
            direction="ltr"
            border={bordered}
            renderers={{
              renderRow,
              noRowsFallback: (
                <StyledTableEmptyWrapper
                  style={{
                    maxWidth: wrapperRef?.current?.clientWidth,
                  }}
                >
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="No data found!"
                  />
                </StyledTableEmptyWrapper>
              ),
            }}
            {...restProps}
          />
        </DndProvider>
      )}
      {loading ? (
        <LoadingView
          position="absolute"
          style={{backgroundColor: 'transparent'}}
        />
      ) : null}
    </React.Fragment>
  );
};

export default AppDraggableDataGrid;
