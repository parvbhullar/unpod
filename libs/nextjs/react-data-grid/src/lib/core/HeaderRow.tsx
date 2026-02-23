import React, {memo, useId, useRef} from 'react';
import styled from 'styled-components';
import {rgba} from 'polished';
import clsx from 'clsx';

import {getColSpan, getMinMaxIdx} from './utils';
import type {
  CalculatedColumn,
  Direction,
  FilterType,
  LocalFilter,
  Maybe,
  Position,
  TableCellItemProps,
  UndoRedoProcessProps,
} from './models/data-grid';
import type {DataGridProps} from './DataGrid';
import {SelectCellState} from './DataGrid';
import HeaderCell from './HeaderCell';
import {CellFrozen, StyledCellWrapper} from './style/cell';
import {rowHidden, rowSelectedClassname} from './style/row';

type SharedDataGridProps<R, SR, K extends React.Key> = Pick<
  DataGridProps<R, SR, K>,
  'sortColumns' | 'onSortColumnsChange' | 'onColumnsReorder'
>;

export type HeaderRowProps<R, SR, K extends React.Key> = SharedDataGridProps<R, SR, K> & {
  rowIdx: number;
  columns: readonly CalculatedColumn<R, SR>[];
  onColumnResize: (
    column: CalculatedColumn<R, SR>,
    width: number | 'max-content',
  ) => void;
  selectCell: (position: Position) => void;
  selectedCellIdx: number | undefined;
  shouldFocusGrid: boolean;
  direction: Direction;

  lastLeftFixedColumnIndex: number;
  isHidden?: boolean;
  showBorder: boolean;
  /*loading: boolean;
  isColumnEditable: boolean;
  measuredColumnWidths: ReadonlyMap<string, number>;*/
  filters: FilterType | undefined;
  rowSelectionType: 'radio' | 'checkbox';
  onFiltersChange?: Maybe<
    Maybe<React.Dispatch<React.SetStateAction<FilterType>>>
  >;
  onInsertCell?: (data: TableCellItemProps) => void;
  onDeleteCells?: (startIdx: number, count: number) => void;
  onRenameColumn?: (columnKey: string, newTitle: string) => void;
  onLocalFiltersChange?: Maybe<
    Maybe<React.Dispatch<React.SetStateAction<LocalFilter[]>>>
  >;
  rowCount: number;
  onSerialNoRowHeaderClick: (cellIdx?: number, rowIdx?: number) => void;
  selectedPosition: SelectCellState;
  draggedOverCellIdx: number;

  saveVersionHistory(data: UndoRedoProcessProps): void;
};

export const StyledHeaderRow = styled.div`
  display: contents;
  line-height: var(--rdg-header-row-height);
  font-weight: bold;

  & > ${StyledCellWrapper} {
    /* Should have a higher value than 1 to show up above regular cells and the focus sink */
    z-index: 2;
    position: sticky;
  }

  & > ${CellFrozen} {
    z-index: 3;
  }

  &.rdg-hidden {
    visibility: hidden;
  }

  & .rdg-cell {
      // background: ${({theme}) => rgba(theme.palette.primary, 0.25)};

    &:first-child {
      border-top-left-radius: 8px;
    }

    &:last-child {
      border-top-right-radius: 8px;

      & .handle-resize {
        border-right: none;
      }
    }
  }
`;

function HeaderRow<R, SR, K extends React.Key>({
                                                 rowIdx,
                                                 columns,
                                                 onColumnResize,
                                                 onColumnsReorder,
                                                 sortColumns,
                                                 onSortColumnsChange,
                                                 selectedCellIdx,
                                                 selectCell,
                                                 shouldFocusGrid,
                                                 direction,

                                                 isHidden,
                                                 filters,
                                                 onFiltersChange,
                                                 lastLeftFixedColumnIndex,
                                                 rowSelectionType,
                                                 showBorder,
                                                 onInsertCell,
                                                 onDeleteCells,
                                                 onRenameColumn,
                                                 onLocalFiltersChange,
                                                 saveVersionHistory,
                                                 rowCount,
                                                 onSerialNoRowHeaderClick,
                                                 selectedPosition,
                                                 draggedOverCellIdx,
                                               }: HeaderRowProps<R, SR, K>) {
  const dragDropKey = useId();
  // For firefox compatibilty
  const isResizedColumn = useRef(false);
  const {idx} = selectedPosition;
  const [startIdx, endIdx] = getMinMaxIdx(idx, draggedOverCellIdx);

  const cells = [];
  for (let index = 0; index < columns.length; index++) {
    const column = columns[index];
    const colSpan = getColSpan(column, lastLeftFixedColumnIndex, {
      type: 'HEADER',
    });
    if (colSpan !== undefined) {
      index += colSpan - 1;
    }

    cells.push(
      <HeaderCell<R, SR>
        key={column.key ?? column.dataIndex}
        column={column}
        colSpan={colSpan}
        rowIdx={rowIdx}
        isCellSelected={selectedCellIdx === column.idx}
        onColumnResize={onColumnResize}
        onColumnsReorder={onColumnsReorder}
        onSortColumnsChange={onSortColumnsChange}
        sortColumns={sortColumns}
        selectCell={selectCell}
        shouldFocusGrid={shouldFocusGrid && index === 0}
        direction={direction}
        dragDropKey={dragDropKey}
        rowSelectionType={rowSelectionType}
        filterValue={filters?.[column.dataIndex]}
        onFiltersChange={onFiltersChange}
        showBorder={showBorder}
        columns={columns}
        onInsertCell={onInsertCell}
        onDeleteCells={onDeleteCells}
        onRenameColumn={onRenameColumn}
        onLocalFiltersChange={onLocalFiltersChange}
        saveVersionHistory={saveVersionHistory}
        onSerialNoRowHeaderClick={onSerialNoRowHeaderClick}
        rowCount={rowCount}
        isResizedColumn={isResizedColumn}
        isPartiallySelected={startIdx <= column.idx && column.idx <= endIdx}
      />,
    );
  }

  return (
    <StyledHeaderRow
      role="row"
      aria-rowindex={rowIdx} // aria-rowindex is 1 based
      className={clsx('rdg-header-row', {
        [rowSelectedClassname]: selectedCellIdx === -1,
        [rowHidden]: isHidden,
      })}
    >
      {cells}
    </StyledHeaderRow>
  );
}

export default memo(HeaderRow) as <R, SR, K extends React.Key>(
  props: HeaderRowProps<R, SR, K>,
) => JSX.Element;
