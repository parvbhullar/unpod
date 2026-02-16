import { useMemo } from 'react';

import { getColSpan } from '../utils';
import type { CalculatedColumn, Maybe } from '../models/data-grid';

type ViewportColumnsArgs<R, SR> = {
  columns: readonly CalculatedColumn<R, SR>[];
  colSpanColumns: readonly CalculatedColumn<R, SR>[];
  rows: readonly R[];
  topSummaryRows: Maybe<readonly SR[]>;
  bottomSummaryRows: Maybe<readonly SR[]>;
  colOverscanStartIdx: number;
  colOverscanEndIdx: number;
  lastLeftFixedColumnIndex: number;
  rowOverscanStartIdx: number;
  rowOverscanEndIdx: number;};

export function useViewportColumns<R, SR>({
  columns,
  colSpanColumns,
  rows,
  topSummaryRows,
  bottomSummaryRows,
  colOverscanStartIdx,
  colOverscanEndIdx,
  lastLeftFixedColumnIndex,
  rowOverscanStartIdx,
  rowOverscanEndIdx,
}: ViewportColumnsArgs<R, SR>) {
  // find the column that spans over a column within the visible columns range and adjust colOverscanStartIdx
  const startIdx = useMemo(() => {
    if (colOverscanStartIdx === 0) return 0;

    let startIdx = colOverscanStartIdx;

    const updateStartIdx = (colIdx: number, colSpan: number | undefined) => {
      if (colSpan !== undefined && colIdx + colSpan > colOverscanStartIdx) {
        startIdx = colIdx;
        return true;
      }
      return false;
    };

    for (const column of colSpanColumns) {
      // check header row
      const colIdx = column.idx;
      if (colIdx >= startIdx) break;
      if (
        updateStartIdx(
          colIdx,
          getColSpan(column, lastLeftFixedColumnIndex, { type: 'HEADER' }),
        )
      ) {
        break;
      }

      // check viewport rows
      for (
        let rowIdx = rowOverscanStartIdx;
        rowIdx <= rowOverscanEndIdx;
        rowIdx++
      ) {
        const row = rows[rowIdx];
        if (
          updateStartIdx(
            colIdx,
            getColSpan(column, lastLeftFixedColumnIndex, { type: 'ROW', row }),
          )
        ) {
          break;
        }
      }

      // check summary rows
      if (topSummaryRows != null) {
        for (const row of topSummaryRows) {
          if (
            updateStartIdx(
              colIdx,
              getColSpan(column, lastLeftFixedColumnIndex, {
                type: 'SUMMARY',
                row,
              }),
            )
          ) {
            break;
          }
        }
      }

      if (bottomSummaryRows != null) {
        for (const row of bottomSummaryRows) {
          if (
            updateStartIdx(
              colIdx,
              getColSpan(column, lastLeftFixedColumnIndex, {
                type: 'SUMMARY',
                row,
              }),
            )
          ) {
            break;
          }
        }
      }
    }

    return startIdx;
  }, [
    rowOverscanStartIdx,
    rowOverscanEndIdx,
    rows,
    topSummaryRows,
    bottomSummaryRows,
    colOverscanStartIdx,
    lastLeftFixedColumnIndex,
    colSpanColumns,
  ]);

  return useMemo((): readonly CalculatedColumn<R, SR>[] => {
    const viewportColumns: CalculatedColumn<R, SR>[] = [];
    for (let colIdx = 0; colIdx <= colOverscanEndIdx; colIdx++) {
      const column = columns[colIdx];

      if (colIdx < startIdx && !column.fixed) continue;
      viewportColumns.push(column);
    }

    // Add right frozen columns to the end of the viewport columns
    // if available to ensure they are always visible in the viewport area
    // when scrolling to the right edge of the table container element (scrollable container).
    // This is necessary because the right frozen columns are not included in the viewport columns
    // when the table is scrolled to the right edge of the table container element. Babulal Kumawat
    const rightFixedColumns = columns.filter(
      (column) => column.fixed === 'right',
    );

    if (rightFixedColumns.length) {
      const updatedViewportColumns = viewportColumns;
      const viewportColumnsKeys = viewportColumns.map((item) => item.key);

      rightFixedColumns.forEach((column) => {
        if (!viewportColumnsKeys.includes(column.dataIndex)) {
          updatedViewportColumns.push(column);
        }
      });

      return updatedViewportColumns;
    }

    return viewportColumns;
  }, [startIdx, colOverscanEndIdx, columns]);
}
