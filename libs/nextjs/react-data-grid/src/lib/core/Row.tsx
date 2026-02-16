import { forwardRef, memo, type RefAttributes } from 'react';
import clsx from 'clsx';

import { RowSelectionProvider, useLatestFunc } from './hooks';
import { getColSpan, getMinMaxIdx, getRowStyle } from './utils';
import type {
  CalculatedColumn,
  CopyClipboardProps,
  RenderRowProps,
} from './models/data-grid';
import Cell from './Cell';
import {
  rowClassname,
  rowSelectedClassname,
  StyledRowWrapper,
} from './style/row';

function Row<R, SR>(
  {
    className,
    rowIdx,
    gridRowStart,
    height,
    selectedCellIdx,
    isRowSelected,
    copiedCellIdx,
    draggedOverCellIdx,
    row,
    viewportColumns,
    selectedCellEditor,
    onCellClick,
    onCellDoubleClick,
    onCellContextMenu,
    rowClass,
    setDraggedOverRowIdx,
    onMouseEnter,
    onRowChange,
    selectCell,

    rowCount,
    rowSelectionType,
    lastLeftFixedColumnIndex,
    showBorder,
    autoRowHeight,
    setDragging,
    setDraggedOverCellIdx,
    selectedCellRange,
    clipboardData,
    latestDraggedOverCellIdx,
    latestDraggedOverRowIdx,
    selectedRowIdx,
    isDraggingLocked,
    unsetRangeSelection,
    onDragSerialNoRow,
    getParsedRow,
    isStickyRowDragRef,
    formulas,
    cellSavedStyles,
    rowKeyId,
    ...props
  }: RenderRowProps<R, SR>,
  ref: React.Ref<HTMLDivElement>,
) {
  const handleRowChange = useLatestFunc(
    (column: CalculatedColumn<R, SR>, newRow: R) => {
      onRowChange(column, rowIdx, newRow);
    },
  );

  function handleDragEnter(event: React.MouseEvent<HTMLDivElement>) {
    // console.log('onMouseEnter Mouse-event: ', event);
    setDraggedOverRowIdx?.(rowIdx);
    onMouseEnter?.(event);
  }

  className = clsx(
    rowClassname,
    `rdg-row-${rowIdx % 2 === 0 ? 'even' : 'odd'}`,
    {
      [rowSelectedClassname]: selectedCellIdx === -1,
      'last-row': rowCount === rowIdx,
    },
    rowClass?.(row, rowIdx),
    className,
  );

  const cells = [];

  const {
    startIdx: copyStartIdx,
    endIdx: copyEndIdx,
    startRowIdx: copyStartRowIdx,
    endRowIdx: copyEndRowIdx,
  } = clipboardData || ({} as CopyClipboardProps);

  const [startRowIdx, endRowIdx] = getMinMaxIdx(
    selectedRowIdx,
    latestDraggedOverRowIdx.current as number,
  );

  const [startIdx, endIdx] = selectedCellRange || [];
  const startCellIdx = Math.min(startIdx as number, endIdx as number);
  const endCellIdx = Math.max(startIdx as number, endIdx as number);

  for (let index = 0; index < viewportColumns.length; index++) {
    const column = viewportColumns[index];
    const { idx } = column;
    const colSpan = getColSpan(column, lastLeftFixedColumnIndex, {
      type: 'ROW',
      row,
    });
    if (colSpan !== undefined) {
      index += colSpan - 1;
    }

    const isCellSelected = selectedCellIdx === idx;

    const isDraggedOver =
      draggedOverCellIdx === idx ||
      (startIdx !== undefined && endIdx !== undefined
        ? startCellIdx <= idx && idx <= endCellIdx
        : false);

    if (isCellSelected && selectedCellEditor) {
      cells.push(selectedCellEditor);
    } else {
      cells.push(
        <Cell
          key={column.key}
          column={column}
          colSpan={colSpan}
          row={row}
          rowIdx={rowIdx}
          isCopied={copiedCellIdx === idx}
          isDraggedOver={isDraggedOver}
          isCellSelected={isCellSelected}
          onClick={onCellClick}
          onDoubleClick={onCellDoubleClick}
          onContextMenu={onCellContextMenu}
          onRowChange={handleRowChange}
          selectCell={selectCell}
          rowSelectionType={rowSelectionType}
          showBorder={showBorder}
          autoRowHeight={autoRowHeight}
          setDragging={setDragging}
          setDraggedOverCellIdx={setDraggedOverCellIdx}
          latestDraggedOverCellIdx={latestDraggedOverCellIdx}
          latestDraggedOverRowIdx={latestDraggedOverRowIdx}
          unsetRangeSelection={unsetRangeSelection}
          isLeftSelectedCell={startCellIdx === idx}
          isRightSelectedCell={endCellIdx === idx}
          isTopSelectedCell={
            startRowIdx === rowIdx && isDraggedOver && !isDraggingLocked
          }
          isBottomSelectedCell={
            endRowIdx === rowIdx && isDraggedOver && !isDraggingLocked
          }
          idx={index}
          isLeftCopiedCell={
            copyStartIdx === idx &&
            copyStartRowIdx <= rowIdx &&
            rowIdx <= copyEndRowIdx
          }
          isRightCopiedCell={
            copyEndIdx === idx &&
            copyStartRowIdx <= rowIdx &&
            rowIdx <= copyEndRowIdx
          }
          isTopCopiedCell={
            copyStartRowIdx === rowIdx &&
            copyStartIdx <= idx &&
            idx <= copyEndIdx
          }
          isBottomCopiedCell={
            copyEndRowIdx === rowIdx && copyStartIdx <= idx && idx <= copyEndIdx
          }
          isPartiallySelected={
            startRowIdx <= rowIdx && rowIdx <= endRowIdx && idx === 0
          }
          onDragSerialNoRow={onDragSerialNoRow}
          isStickyRowDragRef={isStickyRowDragRef}
          columnCount={viewportColumns.length}
          formulas={formulas}
          getParsedRow={getParsedRow}
          cellSavedStyles={cellSavedStyles}
          rowKeyId={rowKeyId}
        />,
      );
    }
  }

  return (
    <RowSelectionProvider value={isRowSelected}>
      <StyledRowWrapper
        role="row"
        ref={ref}
        key={rowIdx}
        className={className}
        onMouseEnter={handleDragEnter}
        style={getRowStyle(gridRowStart, height)}
        {...props}
      >
        {cells}
      </StyledRowWrapper>
    </RowSelectionProvider>
  );
}

const RowComponent = memo(forwardRef(Row)) as <R, SR>(
  props: RenderRowProps<R, SR> & RefAttributes<HTMLDivElement>,
) => JSX.Element;

export default RowComponent;

export function defaultRenderRow<R, SR>(
  key: React.Key,
  props: RenderRowProps<R, SR>,
) {
  return <RowComponent key={key} {...props} />;
}
