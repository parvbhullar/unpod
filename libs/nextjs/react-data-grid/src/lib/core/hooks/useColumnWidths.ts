import { useRef } from 'react';
import { flushSync } from 'react-dom';

import type { CalculatedColumn, StateSetter } from '../models/data-grid';
import { useLayoutEffect } from './useLayoutEffect';
import type { DataGridProps } from '../DataGrid';

export function useColumnWidths<R, SR>(
  columns: readonly CalculatedColumn<R, SR>[],
  viewportColumns: readonly CalculatedColumn<R, SR>[],
  templateColumns: readonly string[],
  gridRef: React.RefObject<HTMLDivElement | null>,
  gridWidth: number,
  resizedColumnWidths: ReadonlyMap<string, number>,
  measuredColumnWidths: ReadonlyMap<string, number>,
  setResizedColumnWidths: StateSetter<ReadonlyMap<string, number>>,
  setMeasuredColumnWidths: StateSetter<ReadonlyMap<string, number>>,
  onColumnResize: DataGridProps<R, SR>['onColumnResize'],
  // Author: Gourav Dev
  isColumnEditable: boolean,
) {
  const prevGridWidthRef = useRef(gridWidth);
  const columnsCanFlex: boolean = columns.length === viewportColumns.length;
  // check if no. of. columns changed // Added by Babulal Kumawat
  const prevNbOfColumns = useRef(columns.length);
  const nbOfColumnsChanged = columns.length !== prevNbOfColumns.current;

  // Allow columns to flex again when...
  const ignorePreviouslyMeasuredColumns: boolean =
    // there is enough space for columns to flex and the grid was resized
    columnsCanFlex &&
    (gridWidth !== prevGridWidthRef.current || nbOfColumnsChanged);

  /*
  // Allow columns to flex again when...
  const ignorePreviouslyMeasuredColumns: boolean =
    // there is enough space for columns to flex and the grid was resized
    columnsCanFlex && gridWidth !== prevGridWidthRef.current;*/

  const newTemplateColumns = [...templateColumns];
  const columnsToMeasure: string[] = [];

  for (const { dataIndex, idx, width } of viewportColumns) {
    // isColumnEditable is used for dynamic columns tables - Gourav Dev
    if (isColumnEditable) {
      if (typeof width === 'string' && !resizedColumnWidths.has(dataIndex)) {
        newTemplateColumns[idx] = width;
        columnsToMeasure.push(dataIndex);
      }
    } else if (
      typeof width === 'string' &&
      (ignorePreviouslyMeasuredColumns ||
        !measuredColumnWidths.has(dataIndex)) &&
      !resizedColumnWidths.has(dataIndex)
    ) {
      newTemplateColumns[idx] = width;
      columnsToMeasure.push(dataIndex);
    }
  }

  const gridTemplateColumns = newTemplateColumns.join(' ');

  useLayoutEffect(() => {
    prevGridWidthRef.current = gridWidth;
    updateMeasuredWidths(columnsToMeasure);
  }, [columnsToMeasure.length]); // added dependency of length to avoid multiple re-renders - Gourav Dev

  function updateMeasuredWidths(columnsToMeasure: readonly string[]) {
    if (columnsToMeasure.length === 0) return;

    setMeasuredColumnWidths((measuredColumnWidths) => {
      const newMeasuredColumnWidths = new Map(measuredColumnWidths);
      let hasChanges = false;

      for (const key of columnsToMeasure) {
        const measuredWidth = measureColumnWidth(gridRef, key);
        hasChanges ||= measuredWidth !== measuredColumnWidths.get(key);
        if (measuredWidth === undefined) {
          newMeasuredColumnWidths.delete(key);
        } else {
          newMeasuredColumnWidths.set(key, measuredWidth);
        }
      }

      return hasChanges ? newMeasuredColumnWidths : measuredColumnWidths;
    });
  }

  function handleColumnResize(
    column: CalculatedColumn<R, SR>,
    nextWidth: number | 'max-content',
  ) {
    const { dataIndex: resizingKey } = column;
    const newTemplateColumns = [...templateColumns];
    const columnsToMeasure: string[] = [];

    // Commented out the below code to allow dynamic columns to resize - Babulal Kumawat
    /*if (column?.fixed && !isNaN(+nextWidth) && +nextWidth > 250) {
      nextWidth = 250;
    }*/

    for (const { dataIndex, idx, width } of viewportColumns) {
      if (resizingKey === dataIndex) {
        const width =
          typeof nextWidth === 'number' ? `${nextWidth}px` : nextWidth;
        newTemplateColumns[idx] = width;
      } else if (
        columnsCanFlex &&
        typeof width === 'string' &&
        !resizedColumnWidths.has(dataIndex)
      ) {
        newTemplateColumns[idx] = width;
        columnsToMeasure.push(dataIndex);
      }
    }

    gridRef.current!.style.gridTemplateColumns = newTemplateColumns.join(' ');
    const measuredWidth =
      typeof nextWidth === 'number'
        ? nextWidth
        : measureColumnWidth(gridRef, resizingKey)!;

    // TODO: remove
    // need flushSync to keep frozen column offsets in sync
    // we may be able to use `startTransition` or even `requestIdleCallback` instead
    flushSync(() => {
      setResizedColumnWidths((resizedColumnWidths) => {
        const newResizedColumnWidths = new Map(resizedColumnWidths);
        newResizedColumnWidths.set(resizingKey, measuredWidth);
        return newResizedColumnWidths;
      });
      updateMeasuredWidths(columnsToMeasure);
    });

    onColumnResize?.(column.idx, measuredWidth);
  }

  return {
    gridTemplateColumns,
    handleColumnResize,
  } as const;
}

function measureColumnWidth(
  gridRef: React.RefObject<HTMLDivElement | null>,
  key: string,
) {
  if (!gridRef.current) return undefined;
  const selector = `[data-measuring-cell-key="${CSS.escape(key)}"]`;
  const measuringCell = gridRef.current.querySelector(selector);

  return measuringCell?.getBoundingClientRect().width;
}
