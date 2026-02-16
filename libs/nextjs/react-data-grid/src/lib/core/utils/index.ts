import type {
  CalculatedColumn,
  CalculatedColumnOrColumnGroup,
} from '../models/data-grid';

export * from './colSpanUtils';
export * from './domUtils';
export * from './eventUtils';
export * from './keyboardUtils';
export * from './renderMeasuringCells';
export * from './selectedCellUtils';
export * from './styleUtils';

export const { min, max, floor, sign, abs } = Math;

export function assertIsValidKeyGetter<R, K extends React.Key>(
  keyGetter: unknown,
): asserts keyGetter is (row: R, rowKey: string) => K {
  if (typeof keyGetter !== 'function') {
    throw new Error('Please specify the rowKeyGetter prop to use selection');
  }
}

export function clampColumnWidth<R, SR>(
  width: number,
  { minWidth, maxWidth }: CalculatedColumn<R, SR>,
): number {
  width = max(width, minWidth);

  // ignore maxWidth if it less than minWidth
  if (typeof maxWidth === 'number' && maxWidth >= minWidth) {
    return min(width, maxWidth);
  }

  return width;
}

export function getHeaderCellRowSpan<R, SR>(
  column: CalculatedColumnOrColumnGroup<R, SR>,
  rowIdx: number,
) {
  return column.parent === undefined
    ? rowIdx
    : column.level - column.parent.level;
}
export function getHeaderCellAlphaIdx(colIndex: number): string {
  let columnLabel = '';

  while (colIndex >= 0) {
    const remainder = colIndex % 26;
    columnLabel = String.fromCharCode(65 + remainder) + columnLabel;
    colIndex = Math.floor(colIndex / 26) - 1;
  }

  return columnLabel;
}

export function getHeaderCellNumIdx(colLabel: string) {
  let colIndex = 0;

  for (let i = 0; i < colLabel.length; i++) {
    colIndex *= 26;
    colIndex += colLabel.charCodeAt(i) - 'A'.charCodeAt(0) + 1;
  }

  return colIndex - 1;
}
