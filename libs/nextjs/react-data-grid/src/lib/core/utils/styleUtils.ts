import type {CSSProperties} from 'react';
import React from 'react';
import clsx from 'clsx';

import type {CalculatedColumn, CalculatedColumnOrColumnGroup,} from '../models/data-grid';
import {
  cellClassname,
  cellFrozenClassname,
  cellFrozenFirstClassname,
  cellFrozenLastClassname,
  cellFrozenRightClassname,
} from '../style/cell';

export function getRowStyle(rowIdx: number, height?: number): CSSProperties {
  if (height !== undefined) {
    return {
      '--rdg-grid-row-start': rowIdx,
      '--rdg-row-height': `${height}px`,
    } as unknown as CSSProperties;
  }
  return {'--rdg-grid-row-start': rowIdx} as unknown as CSSProperties;
}

export function getHeaderCellStyle<R, SR>(
  column: CalculatedColumnOrColumnGroup<R, SR>,
  rowIdx: number,
  rowSpan: number,
): React.CSSProperties {
  const gridRowEnd = rowIdx + 1;
  const paddingBlockStart = `calc(${
    rowSpan - 1
  } * var(--rdg-header-row-height))`;

  if (column.parent === undefined) {
    return {
      insetBlockStart: 0,
      gridRowStart: 1,
      gridRowEnd,
      paddingBlockStart,
    };
  }

  return {
    insetBlockStart: `calc(${rowIdx - rowSpan} * var(--rdg-header-row-height))`,
    gridRowStart: gridRowEnd - rowSpan,
    gridRowEnd,
    paddingBlockStart,
  };
}

export function getCellStyle<R, SR>(
  column: CalculatedColumn<R, SR>,
  colSpan = 1,
): React.CSSProperties {
  const index = column.idx + 1;
  return {
    textAlign: column.align ?? 'left',
    gridColumnStart: index,
    gridColumnEnd: index + colSpan,
    // gridRowEnd: rowSpan !== undefined ? `span ${rowSpan}` : undefined,
    insetInlineStart:
      column.fixed === 'left'
        ? `var(--rdg-frozen-left-${column.idx})`
        : undefined,
    insetInlineEnd:
      column.fixed === 'right'
        ? `var(--rdg-frozen-right-${column.idx})`
        : undefined,
  };
}

export function getCellClassname<R, SR>(
  column: CalculatedColumn<R, SR>,
  ...extraClasses: Parameters<typeof clsx>
): string {
  return clsx(
    cellClassname,
    {
      [cellFrozenClassname]: column.fixed === 'left',
      [cellFrozenRightClassname]: column.fixed === 'right',
      [cellFrozenLastClassname]: column.isLastFrozenColumn,
      [cellFrozenFirstClassname]: column.isFirstFrozenColumn,
    },
    ...extraClasses,
  );
}
