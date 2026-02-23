import {useMemo} from 'react';

import {clampColumnWidth, getHeaderCellAlphaIdx, max, min} from '../utils';
import type {CalculatedColumn, CalculatedColumnParent, ColumnOrColumnGroup, Omit,} from '../models/data-grid';
import {renderValue} from '../cellRenderers';
import type {DataGridProps} from '../DataGrid';
import {SELECT_COLUMN_KEY, SERIAL_COLUMN_KEY} from '../constants/AppConst';

type Mutable<T> = {
  -readonly [P in keyof T]: T[P] extends ReadonlyArray<infer V>
    ? Mutable<V>[]
    : T[P];
};

type WithParent<R, SR> = {
  readonly parent: MutableCalculatedColumnParent<R, SR> | undefined;
};

type MutableCalculatedColumnParent<R, SR> = Omit<
  Mutable<CalculatedColumnParent<R, SR>>,
  'parent'
> &
  WithParent<R, SR>;
type MutableCalculatedColumn<R, SR> = Omit<
  Mutable<CalculatedColumn<R, SR>>,
  'parent'
> &
  WithParent<R, SR>;

type ColumnMetric = {
  width: number;
  left: number;
};

const DEFAULT_COLUMN_WIDTH = 'auto';
const DEFAULT_COLUMN_MIN_WIDTH = 80;

type CalculatedColumnsArgs<R, SR> = {
  rawColumns: readonly ColumnOrColumnGroup<R, SR>[];
  defaultColumnOptions: DataGridProps<R, SR>['defaultColumnOptions'];
  viewportWidth: number;
  scrollLeft: number;
  getColumnWidth: (column: CalculatedColumn<R, SR>) => string | number;
  enableVirtualization: boolean;
};

export function useCalculatedColumns<R, SR>({
                                              rawColumns,
                                              defaultColumnOptions,
                                              getColumnWidth,
                                              viewportWidth,
                                              scrollLeft,
                                              enableVirtualization,
                                            }: CalculatedColumnsArgs<R, SR>) {
  const defaultWidth = defaultColumnOptions?.width ?? DEFAULT_COLUMN_WIDTH;
  const defaultMinWidth =
    defaultColumnOptions?.minWidth ?? DEFAULT_COLUMN_MIN_WIDTH;
  const defaultMaxWidth = defaultColumnOptions?.maxWidth ?? undefined;
  const defaultCellRenderer = defaultColumnOptions?.renderCell ?? renderValue;
  const defaultSortable = defaultColumnOptions?.sorter ?? null;
  const defaultResizable = defaultColumnOptions?.resizable ?? false;
  const defaultDraggable = defaultColumnOptions?.draggable ?? false;

  const {childrenCount} = useMemo(() => {
    let childrenCount = 0;

    for (const rawColumn of rawColumns) {
      if ('children' in rawColumn) {
        childrenCount += rawColumn.children.length - 1;
      }
    }
    return {
      childrenCount,
    };
  }, [rawColumns]);

  const {
    columns,
    colSpanColumns,
    lastLeftFixedColumnIndex,
    lastRightFixedColumnIndex,
    headerRowsCount,
  } = useMemo((): {
    readonly columns: readonly CalculatedColumn<R, SR>[];
    readonly colSpanColumns: readonly CalculatedColumn<R, SR>[];
    readonly headerRowsCount: number;
    readonly lastLeftFixedColumnIndex: number;
    readonly lastRightFixedColumnIndex: number[];
  } => {
    let headerRowsCount = 1;
    const columns: MutableCalculatedColumn<R, SR>[] = [];
    let lastLeftFixedColumnIndex = -1;
    let firstRightFixedColumnIndex = -1;
    const lastRightFixedColumnIndex = [] as number[];
    let rightShadowFrozenColumnIndex = -1;

    collectColumns(rawColumns, 1);

    function collectColumns(
      rawColumns: readonly ColumnOrColumnGroup<R, SR>[],
      level: number,
      parent?: MutableCalculatedColumnParent<R, SR>,
    ) {
      for (const [index, rawColumn] of rawColumns.entries()) {
        if ('children' in rawColumn) {
          const calculatedColumnParent: MutableCalculatedColumnParent<R, SR> = {
            title: rawColumn.title,
            parent,
            idx: -1,
            colSpan: 0,
            level: 0,
            headerCellClass: rawColumn.headerCellClass,
          };

          collectColumns(rawColumn.children, level + 1, calculatedColumnParent);
          continue;
        }

        const frozen = rawColumn.frozen ?? false;
        const fixed = rawColumn.fixed ?? '';

        const column: MutableCalculatedColumn<R, SR> = {
          ...rawColumn,
          parent,
          idx: 0,
          alphaIdx: '',
          level: 0,
          frozen,
          width: rawColumn.width ?? defaultWidth,
          minWidth: rawColumn.minWidth ?? defaultMinWidth,
          maxWidth: rawColumn.maxWidth ?? defaultMaxWidth,
          resizable: rawColumn.resizable ?? defaultResizable,
          draggable: rawColumn.draggable ?? defaultDraggable,
          renderCell: rawColumn.renderCell ?? defaultCellRenderer,
          fixed,
          isLastFrozenColumn: false,
          isFirstRightFixedColumn: false,
          sorter: rawColumn.sorter ?? defaultSortable,
          isFirstFrozenColumn: false,
          sortable: false,
          headerCellOptions: rawColumn.headerCellOptions ?? false,
        };

        columns.push(column);

        if (fixed === 'left') {
          lastLeftFixedColumnIndex++;
        }

        if (fixed === 'right') {
          lastRightFixedColumnIndex.push(index);

          if (firstRightFixedColumnIndex === -1) {
            firstRightFixedColumnIndex = index;
          }
        }

        if (fixed === 'right' && rightShadowFrozenColumnIndex === -1) {
          rightShadowFrozenColumnIndex = index + childrenCount;
        }

        if (level > headerRowsCount) {
          headerRowsCount = level;
        }
      }
    }

    /*const prevFrozenIndex = columns.findIndex((column) => column.frozen);
    const prevFrozenElementKey = columns[prevFrozenIndex - 1]?.key;*/

    columns.sort(
      ({key: aKey, frozen: frozenA}, {key: bKey, frozen: frozenB}) => {
        // Sort select column first:
        if (aKey === SELECT_COLUMN_KEY || aKey === SERIAL_COLUMN_KEY) return -1;
        if (bKey === SELECT_COLUMN_KEY || bKey === SERIAL_COLUMN_KEY) return 1;

        // Sort frozen columns second:
        if (frozenA) {
          if (frozenB) return 0;
          return -1;
        }
        if (frozenB) return 1;

        // TODO: sort columns to keep them grouped if they have a parent

        // Sort other columns last:
        return 0;
      },
    );

    const colSpanColumns: CalculatedColumn<R, SR>[] = [];
    let counter = 0;
    columns.forEach((column, idx) => {
      column.idx = idx;
      if (
        column.dataIndex !== 'serialNoRow' &&
        column.dataIndex !== 'select-row'
      ) {
        column.alphaIdx = getHeaderCellAlphaIdx(counter);
        counter++;
      }
      // column.alphaIdx = idx > 0 ? getHeaderCellAlphaIdx(idx - 1) : '';
      updateColumnParent(column, idx, 0);

      if (column.colSpan != null) {
        colSpanColumns.push(column);
      }
    });

    if (lastLeftFixedColumnIndex !== -1) {
      columns[lastLeftFixedColumnIndex].isLastFrozenColumn = true;
    }

    if (firstRightFixedColumnIndex !== -1) {
      columns[firstRightFixedColumnIndex].isFirstFrozenColumn = true;
    }

    return {
      columns,
      colSpanColumns,
      headerRowsCount,
      lastLeftFixedColumnIndex,
      lastRightFixedColumnIndex,
    };
  }, [
    rawColumns,
    defaultWidth,
    defaultMinWidth,
    defaultMaxWidth,
    defaultCellRenderer,
    defaultResizable,
    defaultSortable,
    defaultDraggable,
  ]);

  const {
    templateColumns,
    layoutCssVars,
    totalLeftFixedColumnWidth,
    columnMetrics,
  } = useMemo((): {
    templateColumns: readonly string[];
    layoutCssVars: Readonly<Record<string, string>>;
    columnMetrics: ReadonlyMap<CalculatedColumn<R, SR>, ColumnMetric>;
    totalLeftFixedColumnWidth: number;
  } => {
    const columnMetrics = new Map<CalculatedColumn<R, SR>, ColumnMetric>();
    let left = 0;
    const templateColumns: string[] = [];
    let totalLeftFixedColumnWidth = 0;

    for (const column of columns) {
      let width = getColumnWidth(column);

      if (typeof width === 'number') {
        width = clampColumnWidth(width, column);
      } else {
        // This is a placeholder width so we can continue to use virtualization.
        // The actual value is set after the column is rendered
        width = column.minWidth;
      }
      templateColumns.push(`${width}px`);
      columnMetrics.set(column, {width, left});
      left += width;
    }

    if (lastLeftFixedColumnIndex !== -1) {
      const columnMetric = columnMetrics.get(
        columns[lastLeftFixedColumnIndex],
      )!;
      totalLeftFixedColumnWidth = columnMetric.left + columnMetric.width;
    }

    const layoutCssVars: Record<string, string> = {};

    for (let i = 0; i <= lastLeftFixedColumnIndex; i++) {
      const column = columns[i];
      layoutCssVars[`--rdg-frozen-left-${column.idx}`] = `${
        columnMetrics.get(column)!.left
      }px`;
    }

    let right = 0;
    for (let i = lastRightFixedColumnIndex.length - 1; i >= 0; i--) {
      const index = lastRightFixedColumnIndex[i];
      const column = columns[index];
      layoutCssVars[`--rdg-frozen-right-${column.idx}`] = `${right}px`;

      right += columnMetrics.get(column)!.width;
    }

    return {
      templateColumns,
      layoutCssVars,
      columnMetrics,
      totalLeftFixedColumnWidth,
    };
  }, [getColumnWidth, columns, lastLeftFixedColumnIndex]);

  const [colOverscanStartIdx, colOverscanEndIdx] = useMemo((): [
    number,
    number,
  ] => {
    if (!enableVirtualization) {
      return [0, columns.length - 1];
    }
    // get the viewport's left side and right side positions for non-frozen columns
    const viewportLeft = scrollLeft + totalLeftFixedColumnWidth;
    const viewportRight = scrollLeft + viewportWidth;
    // get first and last non-frozen column indexes
    const lastColIdx = columns.length - 1;
    const firstUnfrozenColumnIdx = min(
      lastLeftFixedColumnIndex + 1,
      lastColIdx,
    );

    // skip rendering non-frozen columns if the frozen columns cover the entire viewport
    if (viewportLeft >= viewportRight) {
      return [firstUnfrozenColumnIdx, firstUnfrozenColumnIdx];
    }

    // get the first visible non-frozen column index
    let colVisibleStartIdx = firstUnfrozenColumnIdx;
    while (colVisibleStartIdx < lastColIdx) {
      const {left, width} = columnMetrics.get(columns[colVisibleStartIdx])!;
      // if the right side of the columnn is beyond the left side of the available viewport,
      // then it is the first column that's at least partially visible
      if (left + width > viewportLeft) {
        break;
      }
      colVisibleStartIdx++;
    }

    // get the last visible non-frozen column index
    let colVisibleEndIdx = colVisibleStartIdx;
    while (colVisibleEndIdx < lastColIdx) {
      const {left, width} = columnMetrics.get(columns[colVisibleEndIdx])!;
      // if the right side of the column is beyond or equal to the right side of the available viewport,
      // then it the last column that's at least partially visible, as the previous column's right side is not beyond the viewport.
      if (left + width >= viewportRight) {
        break;
      }
      colVisibleEndIdx++;
    }

    const colOverscanStartIdx = max(
      firstUnfrozenColumnIdx,
      colVisibleStartIdx - 1,
    );
    const colOverscanEndIdx = min(lastColIdx, colVisibleEndIdx + 1);

    return [colOverscanStartIdx, colOverscanEndIdx];
  }, [
    columnMetrics,
    columns,
    scrollLeft,
    viewportWidth,
    enableVirtualization,
    lastLeftFixedColumnIndex,
    totalLeftFixedColumnWidth,
  ]);

  return {
    columns,
    colSpanColumns,
    colOverscanStartIdx,
    colOverscanEndIdx,
    templateColumns,
    layoutCssVars,
    headerRowsCount,
    lastLeftFixedColumnIndex,
    totalLeftFixedColumnWidth,
  };
}

function updateColumnParent<R, SR>(
  column: MutableCalculatedColumn<R, SR> | MutableCalculatedColumnParent<R, SR>,
  index: number,
  level: number,
) {
  if (level < column.level) {
    column.level = level;
  }

  if (column.parent !== undefined) {
    const {parent} = column;
    if (parent.idx === -1) {
      parent.idx = index;
    }
    parent.colSpan += 1;
    updateColumnParent(parent, index, level - 1);
  }
}
