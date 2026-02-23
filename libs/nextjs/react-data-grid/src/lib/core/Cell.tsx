import {memo} from 'react';
import styled from 'styled-components';
import {rgba} from 'polished';

import {useRovingTabIndex} from './hooks';
import {createCellEvent, getCellClassname, getCellStyle, isCellEditableUtil,} from './utils';
import type {CellRendererProps} from './models/data-grid';
import {StyledCellWrapper} from './style/cell';

const StyledCell = styled(StyledCellWrapper)`
  transition: background-color 0.3s ease;
  display: flex;
  flex-direction: column;
  justify-content: center;

  &.serial-no-cell {
    background: ${({theme}: { theme: any }) => theme.table.headerBgColor};
    padding: 0;

    & .serial-no-inner-cell {
      height: 100%;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    &.partially-selected {
      &:not(.rdg-cell-dragged-over) {
        border-color: ${({theme}: { theme: any }) =>
  rgba(theme.palette.primary, 0.11)};
      }

      & .serial-no-inner-cell {
        background-color: ${({theme}: { theme: any }) =>
  rgba(theme.palette.primary, 0.11)};
      }
    }

    &.rdg-cell-dragged-over {
      border-color: ${({theme}: { theme: any }) =>
  rgba(theme.palette.primary, 0.11)};

      & .serial-no-inner-cell {
        background-color: ${({theme}: { theme: any }) =>
  rgba(theme.palette.primary, 0.17)};
      }
    }
  }

  &[aria-selected='true'] {
    outline: 2px solid ${({theme}: { theme: any }) => theme.palette.primary};
    outline-offset: -2px;
  }

  &.rdg-cell-copied {
    background-color: ${({theme}: { theme: any }) => theme.copiedBgColor};
  }

  &.rdg-cell-dragged-over:not(.serial-no-cell) {
    background-color: ${({theme}: { theme: any }) =>
  rgba(theme.palette.primary, 0.17)};

    &[aria-selected='true'] {
      outline-width: 2px;
      // outline-offset: 0;
    }
  }

  .editable &::selection,
  .editable & .serial-no-inner-cell::selection {
    background: transparent;
  }

  &.left-selected-cell {
    border-left: 2px solid
      ${({theme}: { theme: any }) => theme.palette.primary} !important;
  }

  &.right-selected-cell {
    border-right: 2px solid
      ${({theme}: { theme: any }) => theme.palette.primary} !important;
  }

  &.top-selected-cell {
    border-top: 2px solid
      ${({theme}: { theme: any }) => theme.palette.primary} !important;
  }

  &.bottom-selected-cell {
    border-bottom: 2px solid
      ${({theme}: { theme: any }) => theme.palette.primary} !important;

    .last-row & {
      border-bottom: 2px solid
        ${({theme}: { theme: any }) => theme.palette.primary} !important;
    }
  }

  &.left-copied-cell {
    border-left: 2px dashed
      ${({theme}: { theme: any }) => theme.palette.primary} !important;
  }

  &.right-copied-cell {
    border-right: 2px dashed
      ${({theme}: { theme: any }) => theme.palette.primary} !important;
  }

  &.top-copied-cell {
    border-top: 2px dashed
      ${({theme}: { theme: any }) => theme.palette.primary} !important;
  }

  &.bottom-copied-cell {
    border-bottom: 2px dashed
      ${({theme}: { theme: any }) => theme.palette.primary} !important;

    .last-row & {
      border-bottom: 2px dashed
        ${({theme}: { theme: any }) => theme.palette.primary} !important;
    }
  }

  & p {
    margin-bottom: 4px;

    &:last-child {
      margin-bottom: 0;
    }
  }
`;

function Cell<R, SR>({
                       column,
                       colSpan,
                       isCellSelected,
                       isCopied,
                       isDraggedOver,
                       row,
                       rowIdx,
                       showBorder,
                       rowSelectionType,
                       onClick,
                       onDoubleClick,
                       onContextMenu,
                       onRowChange,
                       selectCell,
                       autoRowHeight,
                       setDragging,
                       setDraggedOverCellIdx,
                       latestDraggedOverCellIdx,
                       latestDraggedOverRowIdx,
                       isLeftSelectedCell,
                       isRightSelectedCell,
                       isTopSelectedCell,
                       isBottomSelectedCell,
                       isLeftCopiedCell,
                       isRightCopiedCell,
                       isTopCopiedCell,
                       isBottomCopiedCell,
                       isPartiallySelected,
                       unsetRangeSelection,
                       idx,
                       onDragSerialNoRow,
                       isStickyRowDragRef,
                       columnCount,
                       formulas,
                       getParsedRow,
                       cellSavedStyles = [],
                       rowKeyId,
                       ...props
                     }: CellRendererProps<R, SR>) {
  const {tabIndex, childTabIndex, onFocus} =
    useRovingTabIndex(isCellSelected);

  const {cellClass} = column;

  const className = getCellClassname(
    column,
    {
      'rdg-cell-copied': isCopied,
      'rdg-cell-dragged-over': isDraggedOver,
      'show-border': showBorder,
      'rdg-left-selected-cell': isLeftSelectedCell,
      'rdg-right-selected-cell': isRightSelectedCell,
      'rdg-top-selected-cell': isTopSelectedCell,
      'rdg-bottom-selected-cell': isBottomSelectedCell,
      'sticky-row': column.dataIndex === 'serialNoRow',
      'left-selected-cell': isLeftSelectedCell,
      'right-selected-cell': isRightSelectedCell,
      'top-selected-cell': isTopSelectedCell,
      'bottom-selected-cell': isBottomSelectedCell,
      'serial-no-cell': column.dataIndex === 'serialNoRow',
      'left-copied-cell': isLeftCopiedCell,
      'right-copied-cell': isRightCopiedCell,
      'top-copied-cell': isTopCopiedCell,
      'bottom-copied-cell': isBottomCopiedCell,
      'partially-selected': isPartiallySelected,
    },

    typeof cellClass === 'function' ? cellClass(row) : cellClass,
  );
  const isEditable = isCellEditableUtil(column, row);

  function selectCellWrapper(openEditor?: boolean) {
    selectCell(
      {
        rowIdx,
        idx: column.dataIndex === 'serialNoRow' ? column.idx + 1 : column.idx,
        rowKey: row[rowKeyId as keyof R] as string | number,
        colKey: column.dataIndex,
      },
      openEditor,
    );
  }

  function handleClick(event: React.MouseEvent<HTMLDivElement>) {
    unsetRangeSelection();
    // console.log('onClick Mouse-event: ', event);

    if (column.dataIndex === 'serialNoRow') {
      onDragSerialNoRow(columnCount - 1, rowIdx);
    }
    if (onClick) {
      const cellEvent = createCellEvent(event);
      onClick({row, column, selectCell: selectCellWrapper}, cellEvent);
      if (cellEvent.isGridDefaultPrevented()) return;
    }
    selectCellWrapper();
  }

  function handleContextMenu(event: React.MouseEvent<HTMLDivElement>) {
    if (onContextMenu) {
      const cellEvent = createCellEvent(event);
      onContextMenu({row, column, selectCell: selectCellWrapper}, cellEvent);
      if (cellEvent.isGridDefaultPrevented()) return;
    }
    selectCellWrapper();
  }

  function handleDoubleClick(event: React.MouseEvent<HTMLDivElement>) {
    if (onDoubleClick) {
      const cellEvent = createCellEvent(event);
      onDoubleClick({row, column, selectCell: selectCellWrapper}, cellEvent);
      if (cellEvent.isGridDefaultPrevented()) return;
    }
    selectCellWrapper(true);
  }

  function handleRowChange(newRow: R) {
    onRowChange(column, newRow);
  }

  const handleMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
    // console.log('onMouseDown Mouse-event: ', event);
    if (event.buttons !== 1) return;
    setDragging(true);
    selectCellWrapper();

    if (column.dataIndex === 'serialNoRow') {
      isStickyRowDragRef.current = true;
    }
  };

  const handleDragEnter = () => {
    // console.log('onMouseUp Mouse-event: ', rowIdx, column.idx);
    if (isStickyRowDragRef.current) {
      onDragSerialNoRow(columnCount - 1, rowIdx);
    } else if (column.idx > 0) setDraggedOverCellIdx?.(column.idx);
  };

  const handleMouseUp = () => {
    // console.log('onMouseUp Mouse-event: ', event);
    if (isStickyRowDragRef.current) {
      isStickyRowDragRef.current = false;
    }
    const overRowIdx = latestDraggedOverRowIdx.current;
    if (overRowIdx === undefined) return;

    const overCellIdx = latestDraggedOverCellIdx.current;
    if (overCellIdx === undefined) return;

    setDragging(false);
  };

  const rowSpan = column.rowSpan?.({type: 'ROW', row}) ?? undefined;
  const cellFormula =
    formulas?.find(
      (item) =>
        item.colKey === column.dataIndex &&
        item.rowKey === row[rowKeyId as keyof R],
    )?.formula || undefined;
  const cellSavedStyle = cellSavedStyles?.find(
    (item) =>
      item.colKey === column.dataIndex &&
      item.rowKey === row[rowKeyId as keyof R],
  )?.style;

  const updatedRow = getParsedRow(
    row,
    column.dataIndex as keyof R,
    cellFormula,
  );

  const cellContents = () =>
    column.render
      ? column.render(
        updatedRow[column.dataIndex as keyof R],
        updatedRow,
        rowIdx,
      )
      : column.renderCell({
        column,
        row: updatedRow,
        isCellEditable: isEditable,
        tabIndex: childTabIndex,
        onRowChange: handleRowChange,
        rowSelectionType,
      });

  return (
    <StyledCell
      role="gridcell"
      aria-colindex={column.idx + 1} // aria-colindex is 1-based
      aria-selected={isCellSelected}
      aria-colspan={colSpan}
      aria-rowspan={rowSpan}
      aria-readonly={!isEditable || undefined}
      tabIndex={tabIndex}
      className={className}
      style={{...getCellStyle(column, colSpan), ...cellSavedStyle}}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onContextMenu={handleContextMenu}
      onFocus={onFocus}
      $autoRowHeight={autoRowHeight}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseEnter={handleDragEnter}
      {...props}
    >
      {cellContents()}
    </StyledCell>
  );
}

export default memo(Cell) as <R, SR>(
  props: CellRendererProps<R, SR>,
) => JSX.Element;
