import type * as React from 'react';
import {useState} from 'react';
import styled from 'styled-components';
import {rgba} from 'polished';

import {useRovingTabIndex} from './hooks';
import {
  clampColumnWidth,
  getCellClassname,
  getCellStyle,
  getHeaderCellRowSpan,
  getHeaderCellStyle,
  stopPropagation
} from './utils';
import type {
  CalculatedColumn,
  FilterDataType,
  FilterType,
  LocalFilter,
  Maybe,
  SortColumn,
  SortDirection,
  TableCellItemProps,
  UndoRedoProcessProps
} from './models/data-grid';
import type {HeaderRowProps} from './HeaderRow';
import defaultRenderHeaderCell from './renderHeaderCell';
import {StyledCellWrapper} from './style/cell';
import HeaderColumnOptions from './components/HeaderColumnOptions';
import {useDataGridConfiguration} from './DataGridContext';

export const ResizeHandleClassname = styled.div`
  cursor: col-resize;
  position: absolute;
  inset-block-start: 0;
  inset-inline-end: 0;
  inset-block-end: 0;
  inline-size: 9px;
  height: 16px;
  width: 4px;
  margin: auto;
  opacity: 0;
  background-color: #a094ff;
  border-radius: 10px;
`;

export const StyledInnerCell = styled.div`
  padding-block: 0;
  padding-inline: 8px;
  height: 100%;
`;

const CellResizable = styled(StyledCellWrapper)`
  background: ${({theme}: { theme: any }) => theme.table.headerBgColor};
  padding: 0;

  &.cell-frozen {
    z-index: 3 !important;
  }

  &.rdg-cell-resizable {
    touch-action: none;
  }

  &.rdg-cell-sortable {
    cursor: pointer;

    &:hover {
      background: #eae6ff;
    }
  }

  &.partially-selected:not(.serial-no-cell) {
    background: ${({theme}: { theme: any }) => theme.backgroundColor};
    border-color: ${({theme}: { theme: any }) =>
  rgba(theme.palette.primary, 0.15)};

    & ${StyledInnerCell} {
      background-color: ${({theme}: { theme: any }) =>
  rgba(theme.palette.primary, 0.15)};
    }
  }

  &:hover {
    ${ResizeHandleClassname} {
      opacity: 1;
    }
  }

  &:last-child ${ResizeHandleClassname} {
    inset-inline-end: 12px;
  }
`;

type SharedHeaderRowProps<R, SR> = Pick<
  HeaderRowProps<R, SR, React.Key>,
  | 'sortColumns'
  | 'onSortColumnsChange'
  | 'selectCell'
  | 'onColumnResize'
  | 'shouldFocusGrid'
  | 'direction'
  | 'onColumnsReorder'
>;

export type HeaderCellProps<R, SR> = SharedHeaderRowProps<R, SR> & {
  column: CalculatedColumn<R, SR>;
  colSpan: number | undefined;
  rowIdx: number;
  isCellSelected: boolean;
  dragDropKey: string;

  showBorder: boolean;
  filterValue: FilterDataType | undefined;
  onFiltersChange?: Maybe<React.Dispatch<React.SetStateAction<FilterType>>>;
  rowSelectionType: 'radio' | 'checkbox';
  /*measuredColumnWidths: ReadonlyMap<string, number>;
  loading: boolean;
  isColumnEditable: boolean;*/
  columns: readonly CalculatedColumn<R, SR>[];
  onInsertCell?: (data: TableCellItemProps) => void;
  onDeleteCells?: (startIdx: number, count: number) => void;
  onRenameColumn?: (columnKey: string, newTitle: string) => void;
  onLocalFiltersChange?: Maybe<
    Maybe<React.Dispatch<React.SetStateAction<LocalFilter[]>>>
  >;
  rowCount: number;
  isResizedColumn: React.MutableRefObject<boolean>;
  onSerialNoRowHeaderClick: (cellIdx?: number, rowIdx?: number) => void;
  isPartiallySelected?: boolean;

  saveVersionHistory(data: UndoRedoProcessProps): void;
};

export default function HeaderCell<R, SR>({
                                            column,
                                            colSpan,
                                            rowIdx,
                                            isCellSelected,
                                            onColumnResize,
                                            onColumnsReorder,
                                            sortColumns,
                                            onSortColumnsChange,
                                            selectCell,
                                            shouldFocusGrid,
                                            direction,
                                            dragDropKey,
                                            rowSelectionType,
                                            filterValue,
                                            onFiltersChange,
                                            showBorder,
                                            columns,
                                            onInsertCell,
                                            onDeleteCells,
                                            onRenameColumn,
                                            onLocalFiltersChange,
                                            saveVersionHistory,
                                            onSerialNoRowHeaderClick,
                                            rowCount,
                                            isResizedColumn,
                                            isPartiallySelected,
                                          }: HeaderCellProps<R, SR>) {
  const gridConfig = useDataGridConfiguration();
  const [isDragging, setIsDragging] = useState(false);
  const [isOver, setIsOver] = useState(false);
  const [openOptions, setOpenOptions] = useState(false);

  const isRtl = direction === 'rtl';
  const rowSpan = getHeaderCellRowSpan(column, rowIdx);
  const {tabIndex, childTabIndex, onFocus} =
    useRovingTabIndex(isCellSelected);

  const sortIndex = sortColumns?.findIndex(
    (sort) => sort.columnKey === column.dataIndex,
  );

  const sortColumn =
    sortIndex !== undefined && sortIndex > -1
      ? sortColumns![sortIndex]
      : undefined;
  const sortDirection = sortColumn?.direction;
  const priority =
    sortColumn !== undefined && sortColumns!.length > 1
      ? sortIndex! + 1
      : undefined;
  const ariaSort =
    sortDirection && !priority
      ? sortDirection === 'ASC'
        ? 'ascending'
        : 'descending'
      : undefined;

  const {sorter, resizable, draggable} = column;

  const className = getCellClassname(column, column.headerCellClass, {
    'rdg-cell-resizable': resizable,
    'rdg-cell-sortable': sorter,
    'rdg-cell-draggable': draggable,
    'rdg-cell-dragging': isDragging,
    'rdg-cell-drag-over': isOver,
    'show-border': showBorder,
    'serial-no-cell': column.dataIndex === 'serialNoRow',
    'partially-selected': isPartiallySelected,
  });

  const renderHeaderCell = column.renderHeaderCell ?? defaultRenderHeaderCell;

  function onPointerDown(event: React.PointerEvent<HTMLDivElement>) {
    if (event.pointerType === 'mouse' && event.buttons !== 1) {
      return;
    }

    // Fix column resizing on a draggable column in FF
    event.preventDefault();

    const {currentTarget, pointerId} = event;
    const headerCell = currentTarget.parentElement!;
    const {right, left} = headerCell.getBoundingClientRect();
    const offset = isRtl ? event.clientX - left : right - event.clientX;

    function onPointerMove(event: PointerEvent) {
      const {right, left} = headerCell.getBoundingClientRect();
      const width = isRtl
        ? right + offset - event.clientX
        : event.clientX + offset - left;
      if (width > 0) {
        onColumnResize(column, clampColumnWidth(width, column));
      }
    }

    function onLostPointerCapture() {
      currentTarget.removeEventListener('pointermove', onPointerMove);
      currentTarget.removeEventListener(
        'lostpointercapture',
        onLostPointerCapture,
      );
    }

    currentTarget.setPointerCapture(pointerId);
    currentTarget.addEventListener('pointermove', onPointerMove);
    currentTarget.addEventListener('lostpointercapture', onLostPointerCapture);
  }

  function onSort(ctrlClick: boolean, customDir?: SortDirection) {
    const updatedSortDir = customDir ?? sortDirection;

    if (onSortColumnsChange == null) return;
    const {sortDescendingFirst} = column;
    if (sortColumn === undefined) {
      // not currently sorted
      const nextSort: SortColumn = {
        columnKey: column.dataIndex,
        direction: customDir ? customDir : sortDescendingFirst ? 'DESC' : 'ASC',
      };
      onSortColumnsChange(
        sortColumns && ctrlClick ? [...sortColumns, nextSort] : [nextSort],
      );
    } else {
      let nextSortColumn: SortColumn | undefined;
      if (
        (sortDescendingFirst === true && updatedSortDir === 'DESC') ||
        (sortDescendingFirst !== true && updatedSortDir === 'ASC')
      ) {
        nextSortColumn = {
          columnKey: column.dataIndex,
          direction: customDir
            ? customDir
            : updatedSortDir === 'ASC'
              ? 'DESC'
              : 'ASC',
        };
      }
      if (ctrlClick) {
        const nextSortColumns = [...sortColumns!];
        if (nextSortColumn) {
          // swap direction
          nextSortColumns[sortIndex!] = nextSortColumn;
        } else {
          // remove sort
          nextSortColumns.splice(sortIndex!, 1);
        }
        onSortColumnsChange(nextSortColumns);
      } else {
        onSortColumnsChange(nextSortColumn ? [nextSortColumn] : []);
      }
    }
  }

  function onFilter(key: string, value: FilterDataType) {
    onFiltersChange?.((prevState) => {
      const nextState = {...prevState};
      if (!value) {
        delete nextState[key];
      } else {
        nextState[key] = value;
      }
      return nextState;
    });
  }

  function clickHandler(/*event: React.MouseEvent<HTMLSpanElement>*/) {
    if (rowIdx === 1 && column.dataIndex === 'serialNoRow') {
      selectCell({idx: 1, rowIdx: 2});
      onSerialNoRowHeaderClick(columns.length - 1, rowCount - 1);
    } else {
      selectCell({idx: column.idx, rowIdx: rowIdx + 1});
      onSerialNoRowHeaderClick(column.idx, rowCount - 1);
    }
  }

  function onClick(/*event: React.MouseEvent<HTMLSpanElement>*/) {
    if (gridConfig.allowGridActions && gridConfig.allowRangeSelection) {
      const firefoxAgent = navigator.userAgent.indexOf('Firefox') > -1;
      if (firefoxAgent) {
        if (!isResizedColumn.current) {
          clickHandler();
        } else {
          isResizedColumn.current = false;
        }
      } else {
        clickHandler();
      }
    }
  }

  function onDoubleClick() {
    onColumnResize(column, 'max-content');
  }

  function handleFocus(event: React.FocusEvent<HTMLDivElement>) {
    onFocus?.(event);
    if (shouldFocusGrid) {
      // Select the first header cell if there is no selected cell
      selectCell({idx: 0, rowIdx});
    }
  }

  const onContextMenu = (event: React.MouseEvent<HTMLDivElement>) => {
    event.preventDefault();

    if (column.headerCellOptions) setOpenOptions(true);
  };

  // function onKeyDown(event: React.KeyboardEvent<HTMLSpanElement>) {
  //   if (event.key === ' ' || event.key === 'Enter') {
  //     // prevent scrolling
  //     event.preventDefault();
  //     onSort(event.ctrlKey || event.metaKey);
  //   }
  // }

  function onDragStart(event: React.DragEvent<HTMLDivElement>) {
    event.dataTransfer.setData(dragDropKey, column.dataIndex);
    event.dataTransfer.dropEffect = 'move';
    setIsDragging(true);
  }

  function onDragEnd() {
    setIsDragging(false);
  }

  function onDragOver(event: React.DragEvent<HTMLDivElement>) {
    // prevent default to allow drop
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }

  function onDrop(event: React.DragEvent<HTMLDivElement>) {
    setIsOver(false);
    if (event.dataTransfer.types.includes(dragDropKey)) {
      const sourceKey = event.dataTransfer.getData(dragDropKey);
      if (sourceKey !== column.key) {
        event.preventDefault();
        onColumnsReorder?.(sourceKey, column.dataIndex);
      }
    }
  }

  function onDragEnter(event: React.DragEvent<HTMLDivElement>) {
    if (isEventPertinent(event)) {
      setIsOver(true);
    }
  }

  function onDragLeave(event: React.DragEvent<HTMLDivElement>) {
    if (isEventPertinent(event)) {
      setIsOver(false);
    }
  }

  let draggableProps: React.HTMLAttributes<HTMLDivElement> | undefined;
  if (draggable) {
    draggableProps = {
      draggable: true,
      /* events fired on the draggable target */
      onDragStart,
      onDragEnd,
      /* events fired on the drop targets */
      onDragOver,
      onDragEnter,
      onDragLeave,
      onDrop,
    };
  }

  return (
    <CellResizable
      role="columnheader"
      aria-colindex={column.idx + 1}
      aria-colspan={colSpan}
      aria-rowspan={rowSpan}
      aria-selected={isCellSelected}
      aria-sort={ariaSort}
      // set the tabIndex to 0 when there is no selected cell so grid can receive focus
      tabIndex={shouldFocusGrid ? 0 : tabIndex}
      className={className}
      style={{
        ...getHeaderCellStyle(column, rowIdx, rowSpan),
        ...getCellStyle(column, colSpan),
      }}
      onFocus={handleFocus}
      onContextMenu={onContextMenu}
      // onClick={onClick}
      // onKeyDown={column.sorter ? onKeyDown : undefined}
      {...draggableProps}
    >
      <StyledInnerCell>
        {resizable && (
          <ResizeHandleClassname
            className="handle-resize"
            onClick={stopPropagation}
            onDoubleClick={onDoubleClick}
            onPointerDown={onPointerDown}
            onPointerUp={() => {
              isResizedColumn.current = true;
              onSerialNoRowHeaderClick();
            }}
          />
        )}

        {renderHeaderCell({
          column,
          sortDirection,
          priority,
          tabIndex: childTabIndex,
          filterValue,
          onFilter,
          rowSelectionType,
          onSort,
          onClick,
          headerColumnOptions: column.headerCellOptions && (
            <HeaderColumnOptions
              open={openOptions}
              setOpen={setOpenOptions}
              columns={columns}
              column={column}
              onInsertCell={onInsertCell}
              onDeleteCells={onDeleteCells}
              onRenameColumn={onRenameColumn}
              onSort={column.sorter ? onSort : undefined}
              onLocalFiltersChange={onLocalFiltersChange}
              saveVersionHistory={saveVersionHistory}
            />
          ),
        })}
      </StyledInnerCell>
    </CellResizable>
  );
}

// only accept pertinent drag events:
// - ignore drag events going from the container to an element inside the container
// - ignore drag events going from an element inside the container to the container
function isEventPertinent(event: React.DragEvent) {
  const relatedTarget = event.relatedTarget as HTMLElement | null;

  return !event.currentTarget.contains(relatedTarget);
}
