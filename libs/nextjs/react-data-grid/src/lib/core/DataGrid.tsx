import type { CSSProperties, Key, KeyboardEvent, RefAttributes } from 'react';
import React, {
  forwardRef,
  Fragment,
  isValidElement,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
import { flushSync } from 'react-dom';
import clsx from 'clsx';

import {
  RowSelectionChangeProvider,
  RowSelectionProvider,
  useCalculatedColumns,
  useColumnWidths,
  useGridDimensions,
  useLatestFunc,
  useLayoutEffect,
  useViewportColumns,
  useViewportRows,
} from './hooks';
import {
  abs,
  assertIsValidKeyGetter,
  canExitGrid,
  createCellEvent,
  getColSpan,
  getMinMaxIdx,
  getNextSelectedCellPosition,
  isAltKeyHeldDown,
  isCtrlKeyHeldDown,
  isDefaultCellInput,
  isSelectedCellEditable,
  renderMeasuringCells,
  scrollIntoView,
  sign,
} from './utils';
import type {
  CalculatedColumn,
  CellClickArgs,
  CellKeyboardEvent,
  CellKeyDownArgs,
  CellMouseEvent,
  CellNavigationMode,
  CellSelectArgs,
  Column,
  ColumnOrColumnGroup,
  CopyClipboardProps,
  CopyEvent,
  Direction,
  FilterType,
  GridCellStyleType,
  GridConfiguration,
  GridFormulaType,
  GridRowColStyleType,
  LocalFilter,
  Maybe,
  PasteEvent,
  Position,
  Renderers,
  RowsChangeData,
  SelectRowEvent,
  SortColumn,
  TableCellItemProps,
  UndoRedoProcessProps,
} from './models/data-grid';
import { renderCheckbox as defaultRenderCheckbox } from './cellRenderers';
import {
  DataGridDefaultRenderersProvider,
  useDefaultRenderers,
} from './DataGridDefaultRenderersProvider';
import DragHandle from './DragHandle';
import EditCell from './EditCell';
import HeaderRow from './HeaderRow';
import { defaultRenderRow } from './Row';
import type { PartialPosition } from './ScrollToCell';
import ScrollToCell from './ScrollToCell';
import { default as defaultRenderSortStatus } from './sortStatus';
import {
  rootClassname,
  StyledDataGrid,
  StyledTreeGridWrapper,
  viewportDraggingClassname,
} from './style/core';
import SummaryRow from './SummaryRow';
import GroupedColumnHeaderRow from './GroupedColumnHeaderRow';
import ContextWindow from './components/ContextWindow';
import FooterRow from './FooterRow';
import FindAndReplace from './components/FindAndReplace';
import FindRecord from './components/FindRecord';
import { evaluateFormula, isCorrectFormula } from './utils/calculationUtils';
import EditorToolbar from './components/EditorToolbar';
import { DataGridProvider, defaultConfigurations } from './DataGridContext';
import { SERIAL_COLUMN_KEY } from './constants/AppConst';

export type SelectCellState = Position & {
  readonly mode: 'SELECT';
  rowKey: number | string;
  colKey: string;};

export type EditCellState<R> = Position & {
  readonly mode: 'EDIT';
  readonly row: R;
  readonly originalRow: R;};

type DefaultColumnOptions<R, SR> = Pick<
  Column<R, SR>,
  | 'renderCell'
  | 'width'
  | 'minWidth'
  | 'maxWidth'
  | 'resizable'
  | 'sorter'
  | 'draggable'
>;

export type DataGridHandle = {
  element: HTMLDivElement | null;
  scrollToCell: (position: PartialPosition) => void;
  selectCell: (position: Position, enableEditor?: Maybe<boolean>) => void;};

type SharedDivProps = Pick<
  React.HTMLAttributes<HTMLDivElement>,
  | 'role'
  | 'aria-label'
  | 'aria-labelledby'
  | 'aria-describedby'
  | 'aria-rowcount'
  | 'className'
  | 'style'
>;

const serialNoCol = {
  title: '',
  dataIndex: SERIAL_COLUMN_KEY,
  key: SERIAL_COLUMN_KEY,
  dataType: 'number',
  fixed: 'left',
  align: 'center',
  width: '60px',
  resizable: false,
  render: (text: number) => <div className="serial-no-inner-cell">{text}</div>,
};

export type DataGridProps<R, SR = unknown, K extends Key = Key> = SharedDivProps & {
  /**
   * Grid and data Props
   */
  /** An array of objects representing each column on the grid */
  columns: readonly ColumnOrColumnGroup<R, SR>[];
  /** A function called for each rendered row that should return a plain key/value pair object */
  rows: readonly R[];
  /**
   * Rows to be pinned at the top of the rows view for summary, the vertical scroll bar will not scroll these rows.
   */
  topSummaryRows?: Maybe<readonly SR[]>;
  /**
   * Rows to be pinned at the bottom of the rows view for summary, the vertical scroll bar will not scroll these rows.
   */
  bottomSummaryRows?: Maybe<readonly SR[]>;
  /** The getter should return a unique key for each row */
  rowKeyGetter?: Maybe<(row: R, rowKey: string) => K>;
  onRowsChange?: Maybe<(rows: R[], data: RowsChangeData<R, SR>) => void>;
  onColumnChange?: Maybe<(columns: ColumnOrColumnGroup<R, SR>[]) => void>;

  /**
   * Dimensions props
   */
  /**
   * The height of each row in pixels
   * @default 35
   */
  rowHeight?: Maybe<number | ((row: R) => number)>;
  /**
   * The height of the header row in pixels
   * @default 35
   */
  headerRowHeight?: Maybe<number>;
  /**
   * The height of each summary row in pixels
   * @default 35
   */
  summaryRowHeight?: Maybe<number>;

  /**
   * Feature props
   */
  /** Set of selected row keys */
  selectedRows?: Maybe<ReadonlySet<K>>;
  /** Function called whenever row selection is changed */
  onSelectedRowsChange?: Maybe<(selectedRows: Set<K>) => void>;
  /** Used for multi column sorting */
  sortColumns?: Maybe<readonly SortColumn[]>;
  onSortColumnsChange?: Maybe<(sortColumns: SortColumn[]) => void>;
  defaultColumnOptions?: Maybe<DefaultColumnOptions<R, SR>>;
  // onFill?: Maybe<(event: FillEvent<R>) => R>; // Removed by Babulal Kumawat
  onCopy?: Maybe<(event: CopyEvent<R>) => void>;
  onPaste?: Maybe<(event: PasteEvent<R>) => R>;

  /**
   * Event props
   */
  /** Function called whenever a cell is clicked */
  onCellClick?: Maybe<
    (args: CellClickArgs<R, SR>, event: CellMouseEvent) => void
  >;
  /** Function called whenever a cell is double clicked */
  onCellDoubleClick?: Maybe<
    (args: CellClickArgs<R, SR>, event: CellMouseEvent) => void
  >;
  /** Function called whenever a cell is right clicked */
  onCellContextMenu?: Maybe<
    (args: CellClickArgs<R, SR>, event: CellMouseEvent) => void
  >;
  onCellKeyDown?: Maybe<
    (args: CellKeyDownArgs<R, SR>, event: CellKeyboardEvent) => void
  >;
  /** Function called whenever cell selection is changed */
  onSelectedCellChange?: Maybe<(args: CellSelectArgs<R, SR>) => void>;
  /** Called when the grid is scrolled */
  onScroll?: Maybe<(event: React.UIEvent<HTMLDivElement>) => void>;
  /** Called when a column is resized */
  onColumnResize?: Maybe<(idx: number, width: number) => void>;
  /** Called when a column is reordered */
  onColumnsReorder?: Maybe<
    (sourceColumnKey: string, targetColumnKey: string) => void
  >;

  /**
   * Toggles and modes
   */
  /** @default true */
  enableVirtualization?: Maybe<boolean>;

  /**
   * Miscellaneous
   */
  renderers?: Maybe<Renderers<R, SR>>;
  rowClass?: Maybe<(row: R, rowIdx: number) => Maybe<string>>;
  /** @default 'ltr' */
  direction?: Maybe<Direction>;
  'data-testid'?: Maybe<string>;

  /**
   * Grid and data Props
   */
  /** An array of objects representing each column on the grid */
  id?: string;
  rowKey: string;
  rowSelectionType: 'radio' | 'checkbox';
  customGridTemplateRows?: string;
  border?: Maybe<boolean>;
  hidePagination?: boolean;
  filters?: FilterType;
  onFiltersChange?: Maybe<
    Maybe<React.Dispatch<React.SetStateAction<FilterType>>>
  >;
  onLocalFiltersChange?: Maybe<
    Maybe<React.Dispatch<React.SetStateAction<LocalFilter[]>>>
  >;
  /*Add by Babulal Kumawat*/
  autoRowHeight?: boolean;
  onInsertRows?: (
    rowIdx: number,
    count: number,
    callback?: (data: UndoRedoProcessProps) => void,
  ) => void;
  onDeleteRows?: (
    rowIdx: number,
    count: number,
    callback?: (data: UndoRedoProcessProps) => void,
  ) => void;
  onInsertCell?: (
    data: TableCellItemProps,
    callback?: (data: UndoRedoProcessProps) => void,
  ) => void;
  onDeleteCells?: (
    startIdx: number,
    count: number,
    callback?: (data: UndoRedoProcessProps) => void,
  ) => void;
  onRenameColumn?: (
    columnKey: string,
    newTitle: string,
    callback?: (data: UndoRedoProcessProps) => void,
  ) => void;
  formulas?: GridFormulaType[];
  setFormulas?: React.Dispatch<React.SetStateAction<GridFormulaType[]>>;
  cellStyles?: GridCellStyleType[];
  rowColumnStyles?: GridRowColStyleType;
  setCellStyles?: React.Dispatch<React.SetStateAction<GridCellStyleType[]>>;
  setRowColumnStyles?: React.Dispatch<
    React.SetStateAction<GridRowColStyleType>
  >;
  allowGridActions?: boolean;
  configuration?: GridConfiguration;};

const regUniversalNewLine = /^(\r\n|\n\r|\r|\n)/;
const regNextCellNoQuotes = /^[^\t\r\n]+/;
const regNextEmptyCell = /^\t/;

/**
 * Main API Component to render a data grid of rows and columns
 *
 * @example
 *
 * <DataGrid columns={columns} rows={rows} />
 */
function DataGrid<R, SR, K extends Key>(
  props: DataGridProps<R, SR, K>,
  ref: React.Ref<DataGridHandle>,
) {
  const {
    // Grid and data Props
    columns: rawColumns,
    rows: rawRows,
    topSummaryRows,
    bottomSummaryRows,
    rowKeyGetter,
    onRowsChange,
    onColumnChange,
    // Dimensions props
    rowHeight: rawRowHeight,
    headerRowHeight: rawHeaderRowHeight,
    summaryRowHeight: rawSummaryRowHeight,
    // Feature props
    selectedRows,
    onSelectedRowsChange,
    sortColumns,
    onSortColumnsChange,
    defaultColumnOptions,
    // Event props
    onCellClick,
    onCellDoubleClick,
    onCellContextMenu,
    onCellKeyDown,
    onSelectedCellChange,
    onScroll,
    onColumnResize,
    onColumnsReorder,
    onCopy,
    onPaste,
    // Toggles and modes
    enableVirtualization: rawEnableVirtualization,
    // Miscellaneous
    renderers,
    className,
    style,
    rowClass,
    direction: rawDirection,
    // ARIA
    role: rawRole,
    'aria-label': ariaLabel,
    'aria-labelledby': ariaLabelledBy,
    'aria-describedby': ariaDescribedBy,
    'aria-rowcount': rawAriaRowCount,
    'data-testid': testId,
    rowKey,
    rowSelectionType,
    customGridTemplateRows,
    filters,
    onFiltersChange,
    id,
    border,
    autoRowHeight = false,
    onInsertRows,
    onDeleteRows,
    onInsertCell,
    onDeleteCells,
    onRenameColumn,
    onLocalFiltersChange,
    formulas,
    setFormulas,
    cellStyles,
    rowColumnStyles,
    setCellStyles,
    setRowColumnStyles,
    allowGridActions = false,
    configuration,
  } = props;

  /**
   * defaults
   */
  const gridConfig = useMemo(
    () => ({
      ...defaultConfigurations,
      ...configuration,
      allowGridActions,
    }),
    [configuration, allowGridActions],
  );

  const rows: readonly R[] = useMemo(
    () =>
      allowGridActions && gridConfig.showSerialNoRow
        ? [...rawRows].map((item, index) => ({
            ...item,
            [SERIAL_COLUMN_KEY]: index + 1,
          }))
        : rawRows,
    [rawRows, gridConfig],
  );

  const defaultRenderers = useDefaultRenderers<R, SR>();
  const role = rawRole ?? 'grid';
  const rowHeight = rawRowHeight ?? 55;
  const headerRowHeight =
    rawHeaderRowHeight ?? (typeof rowHeight === 'number' ? rowHeight : 55);
  const summaryRowHeight =
    rawSummaryRowHeight ?? (typeof rowHeight === 'number' ? rowHeight : 55);
  const renderRow =
    renderers?.renderRow ?? defaultRenderers?.renderRow ?? defaultRenderRow;
  const renderSortStatus =
    renderers?.renderSortStatus ??
    defaultRenderers?.renderSortStatus ??
    defaultRenderSortStatus;
  const renderCheckbox =
    renderers?.renderCheckbox ??
    defaultRenderers?.renderCheckbox ??
    defaultRenderCheckbox;
  const noRowsFallback =
    renderers?.noRowsFallback ?? defaultRenderers?.noRowsFallback;
  const enableVirtualization = autoRowHeight
    ? false
    : (rawEnableVirtualization ?? true);
  const direction = rawDirection ?? 'ltr';
  const showBorder = border ?? true;
  const undoRef = useRef<UndoRedoProcessProps[]>([]),
    redoRef = useRef<UndoRedoProcessProps[]>([]);
  const isStickyRowDragRef = useRef(false);

  const rowKeyId = rowKey;
  const isColumnEditable =
    rawColumns?.length > 0
      ? isValidElement(rawColumns.slice(-1)[0].title)
      : false;

  /**
   * states
   */
  const [scrollTop, setScrollTop] = useState(0);
  const [scrollLeft, setScrollLeft] = useState(0);
  const [findString, setFindString] = useState('');
  const [findReplaceModalOpen, setFindReplaceModalOpen] = useState(false);
  const [openFindBox, setOpenFindBox] = useState(false);

  const [resizedColumnWidths, setResizedColumnWidths] = useState(
    (): ReadonlyMap<string, number> => new Map(),
  );
  const [measuredColumnWidths, setMeasuredColumnWidths] = useState(
    (): ReadonlyMap<string, number> => new Map(),
  );
  const [copiedCell, setCopiedCell] = useState<{
    row: R;
    columnKey: string;
  } | null>(null);
  const [isDragging, setDragging] = useState(false);
  const [draggedOverRowIdx, setOverRowIdx] = useState<number | undefined>(
    undefined,
  );
  // Added by Babulal Kumawat for selection of cells and rows in grid view
  const [isDraggingLocked, setDraggingLocked] = useState(false);
  const [draggedOverCellIdx, setOverCellIdx] = useState<number | undefined>(
    undefined,
  );
  const [openContextMenu, setOpenContextMenu] = useState(false);

  const [clipboardData, setClipboardData] = useState<CopyClipboardProps | null>(
    null,
  );

  const [scrollToPosition, setScrollToPosition] =
    useState<PartialPosition | null>(null);

  const getColumnWidth = useCallback(
    (column: CalculatedColumn<R, SR>) => {
      return (
        resizedColumnWidths.get(column.dataIndex) ??
        measuredColumnWidths.get(column.dataIndex) ??
        column.width
      );
    },
    [measuredColumnWidths, resizedColumnWidths],
  );

  const [gridRef, gridWidth, gridHeight] = useGridDimensions();
  /*const scrollableNodeRef = React.useRef<HTMLElement>();
  const scrollRef = React.useRef<any>();*/

  const {
    columns,
    colSpanColumns,
    headerRowsCount,
    colOverscanStartIdx,
    colOverscanEndIdx,
    templateColumns,
    layoutCssVars,
    lastLeftFixedColumnIndex,
    totalLeftFixedColumnWidth,
  } = useCalculatedColumns({
    rawColumns:
      allowGridActions &&
      gridConfig.showSerialNoRow &&
      rawColumns?.length > 0 &&
      !rawColumns.find(
        (item) => (item as Column<R, SR>).dataIndex === SERIAL_COLUMN_KEY,
      )
        ? [serialNoCol, ...rawColumns]
        : rawColumns,
    defaultColumnOptions,
    getColumnWidth,
    scrollLeft,
    viewportWidth: gridWidth,
    enableVirtualization,
  });

  const topSummaryRowsCount = topSummaryRows?.length ?? 0;
  const bottomSummaryRowsCount = bottomSummaryRows?.length ?? 0;
  const summaryRowsCount = topSummaryRowsCount + bottomSummaryRowsCount;
  const headerAndTopSummaryRowsCount = headerRowsCount + topSummaryRowsCount;
  const groupedColumnHeaderRowsCount = headerRowsCount - 1;
  const minRowIdx = -headerAndTopSummaryRowsCount;
  const mainHeaderRowIdx = minRowIdx + groupedColumnHeaderRowsCount;
  const maxRowIdx = rows.length + bottomSummaryRowsCount - 1;

  const [selectedPosition, setSelectedPosition] = useState(
    (): SelectCellState | EditCellState<R> => ({
      idx: -1,
      rowIdx: minRowIdx - 1,
      mode: 'SELECT',
      rowKey: '',
      colKey: '',
    }),
  );

  /**
   * refs
   */
  const prevSelectedPosition = useRef(selectedPosition);
  const latestDraggedOverRowIdx = useRef(draggedOverRowIdx);
  const latestDraggedOverCellIdx = useRef(draggedOverCellIdx);
  const lastSelectedRowIdx = useRef(-1);
  const focusSinkRef = useRef<HTMLDivElement>(null);
  const shouldFocusCellRef = useRef(false);

  /**
   * computed values
   */
  const isTreeGrid = role === 'treegrid';
  const headerRowsHeight = headerRowsCount * headerRowHeight;
  const clientHeight =
    gridHeight - headerRowsHeight - summaryRowsCount * summaryRowHeight;
  const isSelectable = selectedRows != null && onSelectedRowsChange != null;
  const isRtl = direction === 'rtl';
  const leftKey = isRtl ? 'ArrowRight' : 'ArrowLeft';
  const rightKey = isRtl ? 'ArrowLeft' : 'ArrowRight';
  const ariaRowCount =
    rawAriaRowCount ?? headerRowsCount + rows.length + summaryRowsCount;

  const defaultGridComponents = useMemo(
    () => ({
      renderCheckbox,
      renderSortStatus,
    }),
    [renderCheckbox, renderSortStatus],
  );

  const allRowsSelected = useMemo((): boolean => {
    // no rows to select = explicitely unchecked
    const { length } = rows;
    return (
      length !== 0 &&
      selectedRows != null &&
      rowKeyGetter != null &&
      selectedRows.size >= length &&
      rows.every((row) => selectedRows.has(rowKeyGetter(row, rowKey)))
    );
  }, [rows, selectedRows, rowKeyGetter, rowKey]);

  const {
    rowOverscanStartIdx,
    rowOverscanEndIdx,
    totalRowHeight,
    gridTemplateRows,
    getRowTop,
    getRowHeight,
    findRowIdx,
  } = useViewportRows({
    rows,
    rowHeight,
    clientHeight,
    scrollTop,
    enableVirtualization,
    autoRowHeight,
  });

  const viewportColumns = useViewportColumns({
    columns,
    colSpanColumns,
    colOverscanStartIdx,
    colOverscanEndIdx,
    lastLeftFixedColumnIndex,
    rowOverscanStartIdx,
    rowOverscanEndIdx,
    rows,
    topSummaryRows,
    bottomSummaryRows,
  });

  const { gridTemplateColumns, handleColumnResize } = useColumnWidths(
    columns,
    viewportColumns,
    templateColumns,
    gridRef,
    gridWidth,
    resizedColumnWidths,
    measuredColumnWidths,
    setResizedColumnWidths,
    setMeasuredColumnWidths,
    onColumnResize,
    isColumnEditable,
  );

  const minColIdx = isTreeGrid ? -1 : 0;
  const maxColIdx = columns.length - 1;
  const selectedCellIsWithinSelectionBounds =
    isCellWithinSelectionBounds(selectedPosition);
  const selectedCellIsWithinViewportBounds =
    isCellWithinViewportBounds(selectedPosition);

  /**
   * The identity of the wrapper function is stable so it won't break memoization
   */
  const handleColumnResizeLatest = useLatestFunc(handleColumnResize);
  const onColumnsReorderLatest = useLatestFunc(onColumnsReorder);
  const onSortColumnsChangeLatest = useLatestFunc(onSortColumnsChange);
  const onCellClickLatest = useLatestFunc(onCellClick);
  const onCellDoubleClickLatest = useLatestFunc(onCellDoubleClick);
  const onCellContextMenuLatest = useLatestFunc(onCellContextMenu);
  const selectRowLatest = useLatestFunc(selectRow);
  const handleFormatterRowChangeLatest = useLatestFunc(updateRow);
  const selectCellLatest = useLatestFunc(selectCell);
  const selectHeaderCellLatest = useLatestFunc(({ idx, rowIdx }: Position) => {
    selectCell({ rowIdx: minRowIdx + rowIdx - 1, idx });
  });
  const onFiltersChangeLatest = useLatestFunc(onFiltersChange);
  const onLocalFiltersChangeLatest = useLatestFunc(onLocalFiltersChange);

  /**
   * effects
   */

  useEffect(() => {
    const zKey = 90,
      hKey = 72,
      fKey = 70;
    const handleKeyDown = (event: any) => {
      if (event?.keyCode === zKey && isCtrlKeyHeldDown(event)) {
        if (isAltKeyHeldDown(event) && redoRef.current.length > 0) {
          onRedo();
        } else if (undoRef.current.length > 1) {
          onUndo();
        }
      } else if (event?.keyCode === hKey && isCtrlKeyHeldDown(event)) {
        event.preventDefault();
        setOpenFindBox(false);
        setFindReplaceModalOpen(true);
      } else if (event?.keyCode === fKey && isCtrlKeyHeldDown(event)) {
        event.preventDefault();
        setOpenFindBox(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  useEffect(() => {
    if (
      allowGridActions &&
      gridConfig.allowUndoRedo &&
      undoRef.current.length === 0 &&
      columns.length > 0
    ) {
      saveVersionHistory({
        rows: [...rows],
        columns: [...columns],
        sortColumns: sortColumns ? [...sortColumns] : [],
        formulas,
        styles: { ...rowColumnStyles, cell: cellStyles },
      });
    }
  }, [columns, allowGridActions, gridConfig]);

  /*useEffect(() => {
    const scrollableNode = scrollableNodeRef.current as HTMLElement;
    const gridNode = gridRef.current as HTMLElement;

    function unregisterEvent() {
      scrollableNode.removeEventListener('scroll', () => {
        gridNode.scrollLeft = scrollableNode.scrollLeft || 0;
      });

      gridNode.removeEventListener('scroll', () => {
        scrollableNode.scrollLeft = gridNode.scrollLeft;
      });
    }

    unregisterEvent();

    scrollableNode.addEventListener('scroll', () => {
      gridNode.scrollLeft = scrollableNode.scrollLeft;
    });

    if (gridNode.scrollWidth !== gridNode.clientWidth) {
      gridNode.classList.add('right-data-scrolled');
    } else {
      gridNode.classList.remove('right-data-scrolled');
    }

    gridRef?.current?.addEventListener('scroll', () => {
      const scrollLeft = gridNode.scrollLeft;

      if (scrollLeft > 0) {
        gridNode.classList.add('left-data-scrolled');
      } else {
        gridNode.classList.remove('left-data-scrolled');
      }

      if (gridNode.scrollWidth >= gridNode.offsetWidth + scrollLeft) {
        gridNode.classList.add('right-data-scrolled');
      } else {
        gridRef?.current?.classList.remove('right-data-scrolled');
      }

      scrollableNode.scrollLeft = scrollLeft;
    });

    return () => {
      unregisterEvent();
    };
  }, [gridRef.current?.scrollWidth]);*/

  useLayoutEffect(() => {
    if (
      !selectedCellIsWithinSelectionBounds ||
      isSamePosition(selectedPosition, prevSelectedPosition.current)
    ) {
      prevSelectedPosition.current = selectedPosition;
      return;
    }

    prevSelectedPosition.current = selectedPosition;

    if (selectedPosition.idx === -1) {
      focusSinkRef.current!.focus({ preventScroll: true });
      scrollIntoView(focusSinkRef.current);
    }
  });

  useLayoutEffect(() => {
    if (!shouldFocusCellRef.current) return;
    shouldFocusCellRef.current = false;
    focusCellOrCellContent();
  });

  /*useLayoutEffect(() => {
    if (!shouldFocusCellRef.current) return;
    shouldFocusCellRef.current = false;
    const cell = getCellToScroll(gridRef.current!);
    if (cell === null) return;

    scrollIntoView(cell);
    // Focus cell content when available instead of the cell itself
    const elementToFocus =
      cell.querySelector<Element & HTMLOrSVGElement>('[tabindex="0"]') ?? cell;
    elementToFocus.focus({ preventScroll: true });
  });*/

  useImperativeHandle(ref, () => ({
    element: gridRef.current,
    scrollToCell({ idx, rowIdx }) {
      const scrollToIdx =
        idx !== undefined &&
        idx > lastLeftFixedColumnIndex &&
        idx < columns.length
          ? idx
          : undefined;
      const scrollToRowIdx =
        rowIdx !== undefined && isRowIdxWithinViewportBounds(rowIdx)
          ? rowIdx
          : undefined;

      if (scrollToIdx !== undefined || scrollToRowIdx !== undefined) {
        setScrollToPosition({ idx: scrollToIdx, rowIdx: scrollToRowIdx });
      }
    },
    selectCell,
  }));

  // Undo and Redo operations
  function setCurrentData(step: UndoRedoProcessProps) {
    if (step?.rows && onRowsChange)
      onRowsChange(step.rows, {
        indexes: [],
        column: {} as CalculatedColumn<R, SR>,
      });

    if (step?.columns && onColumnChange) {
      onColumnChange(
        step.columns.filter((item) => item.dataIndex !== 'serialNoRow'),
      );
    }

    if (step?.sortColumns && onSortColumnsChange) {
      onSortColumnsChange(step.sortColumns);
    }
    if (step?.formulas && setFormulas) {
      setFormulas(step.formulas);
    }
    if (step?.styles) {
      if (setCellStyles && step?.styles?.cell) setCellStyles(step.styles.cell);
      if (setRowColumnStyles && step?.styles?.rows && step?.styles?.columns)
        setRowColumnStyles({
          rows: step?.styles?.rows,
          columns: step?.styles?.columns,
        });
    }
  }

  function onUndo() {
    if (allowGridActions && gridConfig.allowUndoRedo) {
      const X = undoRef.current[undoRef.current.length - 1];
      const Y = undoRef.current[undoRef.current.length - 2];
      undoRef.current.pop();
      redoRef.current.push(X);
      setCurrentData(Y);
    }
  }

  function onRedo() {
    if (allowGridActions && gridConfig.allowUndoRedo) {
      const X = redoRef.current[redoRef.current.length - 1];
      redoRef.current.pop();
      undoRef.current.push(X);
      setCurrentData(X);
    }
  }

  function saveVersionHistory(data: UndoRedoProcessProps) {
    if (allowGridActions && gridConfig.allowUndoRedo) {
      undoRef.current.push({
        ...data,
        columns: data.columns.filter(
          (item) => item.dataIndex !== 'serialNoRow',
        ),
      });
      redoRef.current = [];
    }
  }

  function handleCellEditFinish(row: R, rowIdx: number) {
    const updatedRows = [...rows];
    updatedRows[rowIdx] = row;
    saveVersionHistory({
      rows: updatedRows,
      columns: [...columns],
      sortColumns: sortColumns ? [...sortColumns] : [],
      formulas,
      styles: { ...rowColumnStyles, cell: cellStyles },
    });
  }

  /**
   * callbacks
   */
  const setDraggedOverRowIdx = useCallback((rowIdx?: number) => {
    setOverRowIdx(rowIdx);
    latestDraggedOverRowIdx.current = rowIdx;
  }, []);

  /**
   * Author: Babulal Kumawat
   */
  const setDraggedOverCellIdx = useCallback((cellIdx?: number) => {
    setOverCellIdx(cellIdx);
    latestDraggedOverCellIdx.current = cellIdx;
  }, []);

  /**
   * event handlers
   */
  function selectRow(args: SelectRowEvent<R>) {
    if (!onSelectedRowsChange) return;

    assertIsValidKeyGetter<R, K>(rowKeyGetter);

    if (args.type === 'HEADER') {
      const newSelectedRows = new Set(selectedRows ?? []);
      for (const row of rows) {
        const rowKey = rowKeyGetter?.(row, rowKeyId);
        if (args.checked) {
          newSelectedRows.add(rowKey);
        } else {
          newSelectedRows.delete(rowKey);
        }
      }
      onSelectedRowsChange(newSelectedRows);
      return;
    }

    const { row, checked, isShiftClick } = args;
    const newSelectedRows = new Set(selectedRows ?? []);
    const rowKey = rowKeyGetter?.(row, rowKeyId);
    if (checked) {
      newSelectedRows.add(rowKey);
      const previousRowIdx = lastSelectedRowIdx.current;
      const rowIdx = rows.indexOf(row);
      lastSelectedRowIdx.current = rowIdx;
      if (isShiftClick && previousRowIdx !== -1 && previousRowIdx !== rowIdx) {
        const step = sign(rowIdx - previousRowIdx);
        for (let i = previousRowIdx + step; i !== rowIdx; i += step) {
          const row = rows[i];
          newSelectedRows.add(rowKeyGetter?.(row, rowKeyId));
        }
      }
    } else {
      newSelectedRows.delete(rowKey);
      lastSelectedRowIdx.current = -1;
    }

    onSelectedRowsChange(newSelectedRows);
  }

  function applyStyleProps(styleProps: CSSProperties) {
    if (selectedPosition.idx >= 0) {
      const toggleStyleKeys = ['fontWeight', 'fontStyle', 'textDecoration'];

      const updatedRows = [...rows];
      const updatedCellStyle = [...(cellStyles as GridCellStyleType[])];

      let { columns: columnsSavedStyle, rows: rowsSavedStyle } = {
        ...(rowColumnStyles as GridRowColStyleType),
      };

      // get selected cell style
      const currActiveRow: any = updatedRows[selectedPosition.rowIdx];
      const dataIndex = columns[selectedPosition.idx].dataIndex as keyof R;
      const currDataIndex = dataIndex as string;

      const currentCellStyle = updatedCellStyle?.find(
        (item) =>
          item.rowKey === currActiveRow[rowKeyId] &&
          item.colKey === currDataIndex,
      );

      const currentCellStyleProps =
        currentCellStyle?.style as CSSProperties | null;

      if (draggedOverCellIdx || draggedOverRowIdx) {
        // get start and end indexes
        const [startIdx, endIdx] = getMinMaxIdx(
          selectedPosition.idx,
          draggedOverCellIdx,
        );
        const [startRowIdx, endRowIdx] = getMinMaxIdx(
          selectedPosition.rowIdx,
          draggedOverRowIdx,
        );

        const totalSelectedCols = endIdx - startIdx + 1 + 1; // + serialNoRow;
        const totalSelectedRows = endRowIdx - startRowIdx + 1;
        const rowsLength = rows.length;
        const columnsLength = columns.length;

        let colCount = 0;

        for (let rowIdx = startRowIdx; rowIdx <= endRowIdx; rowIdx++) {
          const row: any = rows[rowIdx];
          let rowColCount = 0;

          let rowSavedStyle =
            rowsSavedStyle?.[row[rowKeyId]] || ({} as CSSProperties);

          for (let cellIdx = startIdx; cellIdx <= endIdx; cellIdx++) {
            const column = columns[cellIdx];
            if (column) {
              const cellStyle = updatedCellStyle?.find(
                (item) =>
                  item.rowKey === row[rowKeyId] &&
                  item.colKey === column.dataIndex,
              );

              const cellStyleIndex = updatedCellStyle.findIndex(
                (item) =>
                  item.rowKey === row[rowKeyId] &&
                  item.colKey === column.dataIndex,
              );

              let cellStyleProps = cellStyle?.style || ({} as CSSProperties);
              let columnSavedStyle =
                columnsSavedStyle?.[currDataIndex] || ({} as CSSProperties);

              for (const cssKey in styleProps) {
                if (
                  currentCellStyleProps?.[cssKey as keyof CSSProperties] &&
                  toggleStyleKeys.includes(cssKey)
                ) {
                  // if cssKey is already present in cell style

                  const {
                    [cssKey as keyof CSSProperties]: value,
                    ...restProps
                  } = cellStyleProps;

                  cellStyleProps = restProps;

                  if (totalSelectedRows === rowsLength && colCount === 0) {
                    columnSavedStyle = Object.keys(columnSavedStyle)
                      .filter((objKey) => objKey !== cssKey)
                      .reduce((styleObj, styleKey) => {
                        return {
                          ...styleObj,
                          [styleKey]:
                            columnSavedStyle[styleKey as keyof CSSProperties],
                        };
                      }, {} as CSSProperties);
                  }

                  if (
                    totalSelectedCols === columnsLength &&
                    rowColCount === 0
                  ) {
                    rowSavedStyle = Object.keys(rowSavedStyle)
                      .filter((objKey) => objKey !== cssKey)
                      .reduce((styleObj, styleKey) => {
                        return {
                          ...styleObj,
                          [styleKey]:
                            rowSavedStyle[styleKey as keyof CSSProperties],
                        };
                      }, {} as CSSProperties);
                  }
                } else {
                  // if cssKey is not present in cell style

                  cellStyleProps = {
                    ...cellStyleProps,
                    [cssKey]: styleProps[cssKey as keyof CSSProperties],
                  };

                  if (totalSelectedRows === rowsLength && colCount === 0) {
                    columnSavedStyle = {
                      ...columnSavedStyle,
                      [cssKey]: styleProps[cssKey as keyof CSSProperties],
                    };
                  }

                  if (
                    totalSelectedCols === columnsLength &&
                    rowColCount === 0
                  ) {
                    rowSavedStyle = {
                      ...rowSavedStyle,
                      [cssKey]: styleProps[cssKey as keyof CSSProperties],
                    };
                  }
                }
              }

              if (cellStyle) {
                updatedCellStyle[cellStyleIndex] = {
                  rowKey: row[rowKeyId],
                  colKey: column.dataIndex as string | number,
                  style: cellStyleProps,
                };
              } else {
                updatedCellStyle.push({
                  rowKey: row[rowKeyId],
                  colKey: column.dataIndex as string | number,
                  style: cellStyleProps,
                });
              }

              if (totalSelectedRows === rowsLength && colCount === 0) {
                columnsSavedStyle = {
                  ...columnsSavedStyle,
                  [currDataIndex]: columnSavedStyle,
                };
              }

              if (totalSelectedCols === columnsLength && rowColCount === 0) {
                rowsSavedStyle = {
                  ...rowsSavedStyle,
                  [row[rowKeyId]]: rowSavedStyle,
                };
              }
            }
            colCount++;
            rowColCount++;
          }

          rowColCount = 0;
        }

        if (
          totalSelectedRows === rowsLength ||
          totalSelectedCols === columnsLength
        ) {
          setRowColumnStyles?.({
            rows: rowsSavedStyle,
            columns: columnsSavedStyle,
          });
        }
      } else {
        const cellStyleIndex = updatedCellStyle.findIndex(
          (item) =>
            item.rowKey === currActiveRow[rowKeyId] &&
            item.colKey === currDataIndex,
        );

        let cellStyleProps = { ...currentCellStyleProps } as CSSProperties;

        for (const cssKey in styleProps) {
          if (
            currentCellStyleProps?.[cssKey as keyof CSSProperties] &&
            toggleStyleKeys.includes(cssKey)
          ) {
            // if cssKey is already present in cell style

            const { [cssKey as keyof CSSProperties]: value, ...restProps } =
              cellStyleProps;

            cellStyleProps = restProps;
          } else {
            // if cssKey is not present in cell style

            cellStyleProps = {
              ...cellStyleProps,
              [cssKey]: styleProps[cssKey as keyof CSSProperties],
            };
          }
        }

        if (currentCellStyle) {
          updatedCellStyle[cellStyleIndex] = {
            rowKey: currActiveRow[rowKeyId],
            colKey: currDataIndex as string | number,
            style: cellStyleProps,
          };
        } else {
          updatedCellStyle.push({
            rowKey: currActiveRow[rowKeyId],
            colKey: currDataIndex as string | number,
            style: cellStyleProps,
          });
        }
      }

      setCellStyles?.([...updatedCellStyle]);

      // save version history for undo/redo
      saveVersionHistory({
        rows: updatedRows,
        columns: [...columns],
        sortColumns: sortColumns ? [...sortColumns] : [],
        formulas,
        styles: {
          columns: columnsSavedStyle,
          rows: rowsSavedStyle,
          cell: [...updatedCellStyle],
        },
      });
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const { idx, rowIdx, mode } = selectedPosition;
    if (mode === 'EDIT' || !allowGridActions) return;

    if (onCellKeyDown && isRowIdxWithinViewportBounds(rowIdx)) {
      const row = rows[rowIdx];
      const cellEvent = createCellEvent(event);
      onCellKeyDown(
        {
          mode: 'SELECT',
          row,
          column: columns[idx],
          rowIdx,
          selectCell,
        },
        cellEvent,
      );
      if (cellEvent.isGridDefaultPrevented()) return;
    }
    if (!(event.target instanceof Element)) return;
    const isCellEvent = event.target.closest('.rdg-cell') !== null;
    const isRowEvent = isTreeGrid && event.target === focusSinkRef.current;
    if (!isCellEvent && !isRowEvent) return;

    const { keyCode } = event;

    if (
      selectedCellIsWithinViewportBounds &&
      // (onPaste != null || onCopy != null) &&
      isCtrlKeyHeldDown(event)
    ) {
      // event.key may differ by keyboard input language, so we use event.keyCode instead
      // event.nativeEvent.code cannot be used either as it would break copy/paste for the DVORAK layout
      const cKey = 67;
      const vKey = 86;
      const xKey = 88;

      if (keyCode === cKey) {
        if (onCopy) {
          // copy highlighted text only
          if (window.getSelection()?.isCollapsed === false) return;
          handleCopy();
        } else handleGridCopy();
        return;
      }
      if (keyCode === xKey) {
        handleGridCopy(handleGridCut);
        return;
      }
      if (keyCode === vKey) {
        if (onPaste != null) handlePaste();
        else handleGridPaste();
        return;
      }
    }

    switch (event.key) {
      case 'Escape':
        setCopiedCell(null);
        return;
      case 'ArrowUp':
      case 'ArrowDown':
      case 'ArrowLeft':
      case 'ArrowRight':
      case 'Tab':
      case 'Home':
      case 'End':
      case 'PageUp':
      case 'PageDown':
        navigate(event);
        break;
      default:
        handleCellInput(event);
        break;
    }
  }

  function handleScroll(event: React.UIEvent<HTMLDivElement>) {
    const { scrollTop, scrollLeft } = event.currentTarget;
    flushSync(() => {
      setScrollTop(scrollTop);
      // scrollLeft is nagative when direction is rtl
      setScrollLeft(abs(scrollLeft));
    });
    onScroll?.(event);
  }

  function updateRow(column: CalculatedColumn<R, SR>, rowIdx: number, row: R) {
    if (typeof onRowsChange !== 'function') return;
    if (row === rows[rowIdx]) return;
    const updatedRows = [...rows];
    updatedRows[rowIdx] = row;
    onRowsChange(updatedRows, {
      indexes: [rowIdx],
      column,
    });
  }

  function updateCellWizeFormula(
    formulas: GridFormulaType[],
    position: SelectCellState | EditCellState<R>,
    dataIndex: keyof R,
    formula: string,
  ) {
    setFormulas?.(formulas);
    const updatedRows = [...rows];

    updatedRows[position.rowIdx] = {
      ...updatedRows[position.rowIdx],
      [dataIndex]: formula,
    };

    onRowsChange?.(updatedRows, {
      indexes: [],
      column: {} as CalculatedColumn<R, SR>,
    });

    saveVersionHistory({
      rows: updatedRows,
      columns: [...columns],
      sortColumns: sortColumns ? [...sortColumns] : [],
      formulas,
      styles: { ...rowColumnStyles, cell: cellStyles },
    });
  }

  function updateFormulaChanges(
    position: SelectCellState | EditCellState<R>,
    customValue?: string,
  ) {
    if (gridConfig.allowFormula) {
      const dataIndex = columns[position.idx].dataIndex as keyof R;
      const rowId = rows[position.rowIdx]?.[rowKey as keyof R];
      const selectedCellValue =
        customValue ??
        ((position as EditCellState<R>)?.row?.[dataIndex] as string);

      if (formulas) {
        const foundFormulaIndex = formulas.findIndex(
          (item) => item.colKey === dataIndex && item.rowKey === rowId,
        );

        if (isCorrectFormula(String(selectedCellValue))) {
          if (foundFormulaIndex >= 0) {
            // if formula is found at index and formula is updated

            const updatedTableFormula = [...formulas];
            updatedTableFormula[foundFormulaIndex] = {
              ...updatedTableFormula[foundFormulaIndex],
              formula: selectedCellValue as string,
            };
            updateCellWizeFormula(
              updatedTableFormula,
              position,
              dataIndex,
              selectedCellValue as string,
            );
          } else {
            // if formula is not found at index and formula is added

            const newFormulaObj: GridFormulaType = {
              colKey: dataIndex as string,
              rowKey: rowId as string | number,
              formula: selectedCellValue as string,
            };
            const updatedTableFormula = [...formulas, newFormulaObj];

            updateCellWizeFormula(
              updatedTableFormula,
              position,
              dataIndex,
              selectedCellValue as string,
            );
          }
        } else if (foundFormulaIndex >= 0) {
          // if formula is found at index and is replaced with non-formula value

          const updatedTableFormula = formulas.filter(
            (_, index) => index !== foundFormulaIndex,
          );
          setFormulas?.(updatedTableFormula);
          saveVersionHistory({
            rows: [...rows],
            columns: [...columns],
            sortColumns: sortColumns ? [...sortColumns] : [],
            formulas: updatedTableFormula,
            styles: { ...rowColumnStyles, cell: cellStyles },
          });
        }
      }
    }
  }

  function commitEditorChanges() {
    if (selectedPosition.mode !== 'EDIT') return;
    updateFormulaChanges(selectedPosition);
    updateRow(
      columns[selectedPosition.idx],
      selectedPosition.rowIdx,
      selectedPosition.row,
    );
  }

  function handleCopy() {
    const { idx, rowIdx } = selectedPosition;
    const sourceRow = rows[rowIdx];
    const sourceColumnKey = columns[idx].dataIndex;
    setCopiedCell({ row: sourceRow, columnKey: sourceColumnKey });
    onCopy?.({ sourceRow, sourceColumnKey });
  }

  function handlePaste() {
    if (
      !onPaste ||
      !onRowsChange ||
      copiedCell === null ||
      !isCellEditable(selectedPosition)
    ) {
      return;
    }

    const { idx, rowIdx } = selectedPosition;
    const targetColumn = columns[idx];
    const targetRow = rows[rowIdx];

    const updatedTargetRow = onPaste({
      sourceRow: copiedCell.row,
      sourceColumnKey: copiedCell.columnKey,
      targetRow,
      targetColumnKey: targetColumn.dataIndex,
    });

    updateRow(targetColumn, rowIdx, updatedTargetRow);
  }

  /**
   * Decode spreadsheet string into array.
   *
   * @param {string} str The string to parse.
   * @returns {Array}
   */
  function parse(str: string) {
    const arr = [['']];

    if (str.length === 0) {
      return arr;
    }

    let column = 0;
    let row = 0;
    let lastLength = 0;

    while (str.length > 0) {
      if (lastLength === str.length) {
        // In the case If in last cycle we didn't match anything, we have to leave the infinite loop
        break;
      }

      lastLength = str.length;

      if (str.match(regNextEmptyCell)) {
        str = str.replace(regNextEmptyCell, '');

        column += 1;
        arr[row][column] = '';
      } else if (str.match(regUniversalNewLine)) {
        str = str.replace(regUniversalNewLine, '');
        column = 0;
        row += 1;

        arr[row] = [''];
      } else {
        let nextCell = '';

        if (str.startsWith('"')) {
          let quoteNo = 0;
          let isStillCell = true;

          while (isStillCell) {
            const nextChar = str.slice(0, 1);

            if (nextChar === '"') {
              quoteNo += 1;
            }

            nextCell += nextChar;

            str = str.slice(1);

            if (
              str.length === 0 ||
              (str.match(/^[\t\r\n]/) && quoteNo % 2 === 0)
            ) {
              isStillCell = false;
            }
          }

          nextCell = nextCell
            .replace(/^"/, '')
            .replace(/"$/, '')
            .replace(/["]*/g, (match) =>
              new Array(Math.floor(match.length / 2)).fill('"').join(''),
            );
        } else {
          const matchedText = str.match(regNextCellNoQuotes);

          nextCell = matchedText ? matchedText[0] : '';
          str = str.slice(nextCell.length);
        }

        arr[row][column] = nextCell;
      }
    }

    return arr;
  }

  /**
   * Handle keyboard paste event in the grid
   */
  const handleGridPaste = () => {
    if (typeof onRowsChange !== 'function') return;

    if (selectedCellIsWithinViewportBounds) {
      navigator.clipboard
        .readText()
        .then((pastedData) => {
          if (pastedData) {
            const parsedData = parse(pastedData);
            const { idx, rowIdx } = selectedPosition;
            const column = columns[idx];
            const updatedRows = [...rows];

            let rowIndex = rowIdx - 1;
            let lastRowIdx = rowIdx;
            let lastColumnIdx = idx;
            const newRows = [];

            for (let i = 0; i < parsedData.length; i++) {
              rowIndex += 1;
              const row: any = { ...(rows[rowIndex] ?? {}) };
              let columnIndex = idx - 1;

              for (let j = 0; j < parsedData[i].length; j++) {
                columnIndex += 1;
                const cell = columns[columnIndex];
                if (cell) {
                  row[cell.dataIndex] = parsedData[i][j];
                  lastColumnIdx = columnIndex;
                } else {
                  break;
                }
              }

              updatedRows[rowIndex] = row;
              newRows.push(row);
              lastRowIdx = rowIndex;
            }

            if (
              clipboardData &&
              pastedData.replace(/(\r\n|\n|\r)/gm, '') ===
                clipboardData.content.replace(/(\r\n|\n|\r)/gm, '')
            ) {
              const { startRowIdx, endRowIdx, startIdx, endIdx } =
                clipboardData;
              for (let i = startRowIdx; i <= endRowIdx; i++) {
                const row: any = { ...(rows[i] ?? {}) };

                for (let j = startIdx; j <= endIdx; j++) {
                  const cell = columns[j];
                  row[cell.dataIndex] = '';
                }

                updatedRows[i] = row;
              }
            }

            setClipboardData(null);

            saveVersionHistory({
              rows: updatedRows,
              columns: [...columns],
              sortColumns: sortColumns ? [...sortColumns] : [],
              formulas,
            });

            onRowsChange(updatedRows, {
              indexes: [rowIdx],
              column: column,
            });

            setDraggedOverRowIdx(lastRowIdx);
            setDraggedOverCellIdx(lastColumnIdx);
          }
        })
        .catch((error) => {
          console.log('Data copied to clipboard error', error);
        });
    }
  };

  /**
   * Handle keyboard copy event in the grid
   * @param callback
   */
  const handleGridCopy = (callback?: (data: CopyClipboardProps) => void) => {
    const { idx, rowIdx, mode } = selectedPosition;
    if (mode === 'EDIT') return;

    if (selectedCellIsWithinViewportBounds) {
      const [startIdx, endIdx] = getMinMaxIdx(idx, draggedOverCellIdx);
      const [startRowIdx, endRowIdx] = getMinMaxIdx(rowIdx, draggedOverRowIdx);

      const rowsData: string[] = [];

      for (let i = startRowIdx; i <= endRowIdx; i++) {
        const row: any = rows[i];
        const columnsData = [];

        for (let j = startIdx; j <= endIdx; j++) {
          const cell = columns[j];
          if (cell) {
            columnsData.push(row[cell.dataIndex]);
          }
        }

        rowsData.push(columnsData.join('\t'));
      }

      const data = rowsData.join('\n');

      navigator.clipboard
        .writeText(data)
        .then(() => {
          if (callback) {
            callback({
              startIdx,
              startRowIdx,
              endIdx,
              endRowIdx,
              content: data,
            });
          } else {
            setClipboardData({
              startIdx,
              startRowIdx,
              endIdx,
              endRowIdx,
              content: '',
            });
          }
        })
        .catch((error) => {
          console.log('Data copied to clipboard error', error);
        });
    }
  };

  /**
   * Handle keyboard cut event in the grid
   * @param data CopyClipboardProps
   */
  const handleGridCut = (data: CopyClipboardProps) => {
    setClipboardData(data);
  };

  function handleCellInput(event: KeyboardEvent<HTMLDivElement>) {
    if (!selectedCellIsWithinViewportBounds) return;
    const row = rows[selectedPosition.rowIdx];
    const { key, shiftKey } = event;

    // Select the row on Shift + Space
    if (isSelectable && shiftKey && key === ' ') {
      assertIsValidKeyGetter<R, K>(rowKeyGetter);
      if (rowKeyGetter) {
        const rowKey = rowKeyGetter(row, rowKeyId);
        selectRow({
          type: 'ROW',
          row,
          checked: !selectedRows?.has(rowKey),
          isShiftClick: false,
        });
      }
      // do not scroll
      event.preventDefault();
      return;
    }

    if (isCellEditable(selectedPosition) && isDefaultCellInput(event)) {
      setSelectedPosition(({ idx, rowIdx }) => ({
        idx,
        rowIdx,
        mode: 'EDIT',
        row,
        originalRow: row,
      }));
    }
  }

  /**
   * Author: Babulal Kumawat
   */

  const unsetRangeSelection = useCallback(() => {
    setDragging(false);
    setDraggedOverCellIdx(undefined);
    setDraggedOverRowIdx(undefined);
  }, []);

  const selectSerialNoRow = useCallback(
    (cellIdx?: number, rowIdx?: number) => {
      if (allowGridActions && gridConfig.allowRangeSelection) {
        setDraggedOverCellIdx(cellIdx);
        setDraggedOverRowIdx(rowIdx);
        setDragging(false);
      }
    },
    [gridConfig, allowGridActions],
  );

  const onContextMenuClick = (
    args: CellClickArgs<R, SR>,
    event: CellMouseEvent,
  ) => {
    if (onCellContextMenuLatest) {
      onCellContextMenuLatest(args, event);
    } else if (gridConfig.allowContextMenu) {
      event.preventGridDefault();
      // Do not show the default context menu
      event.preventDefault();
      const { idx, rowIdx } = selectedPosition;
      let isCellSelectedWithinRange = false;

      if (draggedOverCellIdx && draggedOverRowIdx) {
        const [startIdx, endIdx] = getMinMaxIdx(idx, draggedOverCellIdx);
        const [startRowIdx, endRowIdx] = getMinMaxIdx(
          rowIdx,
          draggedOverRowIdx,
        );

        const cellIdx = columns.indexOf(args.column);
        const rowIndex = rows.indexOf(args.row);

        if (
          startIdx <= cellIdx &&
          cellIdx <= endIdx &&
          startRowIdx <= rowIndex &&
          rowIndex <= endRowIdx
        ) {
          isCellSelectedWithinRange = true;
        }
      }

      if (!isCellSelectedWithinRange) {
        setDraggedOverCellIdx(undefined);
        setDraggedOverRowIdx(undefined);
        args.selectCell();
      }
      setOpenContextMenu(true);
    }
  };

  const onCloseContextModal = () => {
    setOpenContextMenu(false);
  };

  /**
   * utils
   */
  function isColIdxWithinSelectionBounds(idx: number) {
    return idx >= minColIdx && idx <= maxColIdx;
  }

  function isRowIdxWithinViewportBounds(rowIdx: number) {
    return rowIdx >= 0 && rowIdx < rows.length;
  }

  function isCellWithinSelectionBounds({ idx, rowIdx }: Position): boolean {
    return (
      rowIdx >= minRowIdx &&
      rowIdx <= maxRowIdx &&
      isColIdxWithinSelectionBounds(idx)
    );
  }

  function isCellWithinEditBounds({ idx, rowIdx }: Position): boolean {
    return isRowIdxWithinViewportBounds(rowIdx) && idx >= 0 && idx <= maxColIdx;
  }

  function isCellWithinViewportBounds({ idx, rowIdx }: Position): boolean {
    return (
      isRowIdxWithinViewportBounds(rowIdx) && isColIdxWithinSelectionBounds(idx)
    );
  }

  function isCellEditable(position: Position): boolean {
    return (
      isCellWithinEditBounds(position) &&
      isSelectedCellEditable({ columns, rows, selectedPosition: position })
    );
  }

  function selectCell(
    position: Position | SelectCellState,
    enableEditor?: Maybe<boolean>,
  ): void {
    if (!isCellWithinSelectionBounds(position) || !allowGridActions) return;
    commitEditorChanges();

    const row = rows[position.rowIdx];
    const samePosition = isSamePosition(selectedPosition, position);

    if (enableEditor && isCellEditable(position)) {
      setSelectedPosition({ ...position, mode: 'EDIT', row, originalRow: row });
    } else if (samePosition) {
      // Avoid re-renders if the selected cell state is the same
      scrollIntoView(getCellToScroll(gridRef.current!));
    } else {
      shouldFocusCellRef.current = true;
      setSelectedPosition({ ...position, mode: 'SELECT' } as SelectCellState);
    }

    if (onSelectedCellChange && !samePosition) {
      onSelectedCellChange({
        rowIdx: position.rowIdx,
        row,
        column: columns[position.idx],
      });
    }
  }

  function getNextPosition(
    key: string,
    ctrlKey: boolean,
    shiftKey: boolean,
  ): Position {
    const { idx, rowIdx } = selectedPosition;
    const isRowSelected = selectedCellIsWithinSelectionBounds && idx === -1;

    switch (key) {
      case 'ArrowUp':
        return { idx, rowIdx: rowIdx - 1 };
      case 'ArrowDown':
        return { idx, rowIdx: rowIdx + 1 };
      case leftKey:
        return { idx: idx - 1, rowIdx };
      case rightKey:
        return { idx: idx + 1, rowIdx };
      case 'Tab':
        return { idx: idx + (shiftKey ? -1 : 1), rowIdx };
      case 'Home':
        // If row is selected then move focus to the first row
        if (isRowSelected) return { idx, rowIdx: minRowIdx };
        return { idx: 0, rowIdx: ctrlKey ? minRowIdx : rowIdx };
      case 'End':
        // If row is selected then move focus to the last row.
        if (isRowSelected) return { idx, rowIdx: maxRowIdx };
        return { idx: maxColIdx, rowIdx: ctrlKey ? maxRowIdx : rowIdx };
      case 'PageUp': {
        if (selectedPosition.rowIdx === minRowIdx) return selectedPosition;
        const nextRowY =
          getRowTop(rowIdx) + getRowHeight(rowIdx) - clientHeight;
        return { idx, rowIdx: nextRowY > 0 ? findRowIdx(nextRowY) : 0 };
      }
      case 'PageDown': {
        if (selectedPosition.rowIdx >= rows.length) return selectedPosition;
        const nextRowY = getRowTop(rowIdx) + clientHeight;
        return {
          idx,
          rowIdx:
            nextRowY < totalRowHeight ? findRowIdx(nextRowY) : rows.length - 1,
        };
      }
      default:
        return selectedPosition;
    }
  }

  function navigate(event: KeyboardEvent<HTMLDivElement>) {
    if (!allowGridActions) return;

    const { key, shiftKey } = event;
    let cellNavigationMode: CellNavigationMode = 'NONE';
    if (key === 'Tab') {
      if (
        canExitGrid({
          shiftKey,
          maxColIdx,
          minRowIdx,
          maxRowIdx,
          selectedPosition,
        })
      ) {
        commitEditorChanges();
        // Allow focus to leave the grid so the next control in the tab order can be focused
        return;
      }

      cellNavigationMode = 'CHANGE_ROW';
    }

    // Do not allow focus to leave and prevent scrolling
    event.preventDefault();

    const ctrlKey = isCtrlKeyHeldDown(event);
    const nextPosition = getNextPosition(key, ctrlKey, shiftKey);
    if (isSamePosition(selectedPosition, nextPosition)) return;

    const nextSelectedCellPosition = getNextSelectedCellPosition({
      moveUp: key === 'ArrowUp',
      moveNext: key === rightKey || (key === 'Tab' && !shiftKey),
      columns,
      colSpanColumns,
      rows,
      topSummaryRows,
      bottomSummaryRows,
      minRowIdx,
      mainHeaderRowIdx,
      maxRowIdx,
      lastLeftFixedColumnIndex,
      cellNavigationMode,
      currentPosition: selectedPosition,
      nextPosition,
      isCellWithinBounds: isCellWithinSelectionBounds,
    });

    selectCell(nextSelectedCellPosition);
  }

  function getDraggedOverCellIdx(currentRowIdx: number): number | undefined {
    if (draggedOverRowIdx === undefined) return;
    const { rowIdx } = selectedPosition;

    const isDraggedOver =
      rowIdx < draggedOverRowIdx
        ? rowIdx < currentRowIdx && currentRowIdx <= draggedOverRowIdx
        : rowIdx > currentRowIdx && currentRowIdx >= draggedOverRowIdx;

    return isDraggedOver ? selectedPosition.idx : undefined;
  }

  function getSelectedCellRange(
    currentRowIdx: number,
  ): [number, number] | undefined {
    if (draggedOverRowIdx === undefined) return;
    if (draggedOverCellIdx === undefined) return;
    const { rowIdx } = selectedPosition;

    const isDraggedOver =
      rowIdx < draggedOverRowIdx
        ? rowIdx <= currentRowIdx && currentRowIdx <= draggedOverRowIdx
        : rowIdx >= currentRowIdx && currentRowIdx >= draggedOverRowIdx;

    return isDraggedOver
      ? [selectedPosition.idx, draggedOverCellIdx]
      : undefined;
  }

  function focusCellOrCellContent() {
    const cell = getCellToScroll(gridRef.current!);
    if (cell === null) return;

    scrollIntoView(cell);
    // Focus cell content when available instead of the cell itself
    const elementToFocus =
      cell.querySelector<Element & HTMLOrSVGElement>('[tabindex="0"]') ?? cell;
    elementToFocus.focus({ preventScroll: true });
  }

  function renderDragHandle() {
    if (
      !gridConfig.allowEditCell ||
      selectedPosition.mode === 'EDIT' ||
      !isCellWithinViewportBounds(selectedPosition)
    ) {
      return;
    }

    const { idx, rowIdx } = selectedPosition;
    const column = columns[idx];
    if (
      column.renderEditCell == null ||
      column.editable === false ||
      (draggedOverCellIdx && draggedOverCellIdx !== idx) ||
      (!isDraggingLocked && draggedOverRowIdx && draggedOverRowIdx !== rowIdx)
    ) {
      return;
    }

    const columnWidth = getColumnWidth(column);

    return (
      <DragHandle
        gridRowStart={headerAndTopSummaryRowsCount + rowIdx + 1}
        rows={rows}
        column={column}
        columnWidth={columnWidth}
        maxColIdx={maxColIdx}
        isLastRow={rowIdx === maxRowIdx}
        selectedPosition={selectedPosition}
        isCellEditable={isCellEditable}
        latestDraggedOverRowIdx={latestDraggedOverRowIdx}
        onRowsChange={(updatedRows, data) => {
          onRowsChange?.(updatedRows, data);
          saveVersionHistory({
            rows: updatedRows,
            columns: [...columns],
            sortColumns: sortColumns ? [...sortColumns] : [],
            formulas,
            styles: { ...rowColumnStyles, cell: cellStyles },
          });
        }}
        onClick={focusCellOrCellContent}
        setDragging={(isActive) => {
          setDraggingLocked(isActive);
          setDragging(isActive);
        }}
        setDraggedOverRowIdx={setDraggedOverRowIdx}
      />
    );
  }

  function getParsedRow(row: R, dataIndex: keyof R, formula?: string): R {
    if (formula && isCorrectFormula(String(formula)))
      return {
        ...row,
        [dataIndex]: evaluateFormula(rows, columns, formula),
      };
    else if (
      String(row[dataIndex])?.startsWith('=') &&
      isCorrectFormula(String(row[dataIndex]))
    )
      return {
        ...row,
        [dataIndex]: evaluateFormula(rows, columns, row[dataIndex] as string),
      };

    return row;
  }

  function getCellEditor(rowIdx: number) {
    if (
      !gridConfig.allowEditCell ||
      selectedPosition.rowIdx !== rowIdx ||
      selectedPosition.mode === 'SELECT'
    )
      return;

    const { idx, row } = selectedPosition;
    const column = columns[idx];
    const colSpan = getColSpan(column, lastLeftFixedColumnIndex, {
      type: 'ROW',
      row,
    });

    const closeEditor = (shouldFocusCell: boolean) => {
      if (selectedPosition.mode === 'EDIT')
        updateFormulaChanges(selectedPosition);

      shouldFocusCellRef.current = shouldFocusCell;
      setSelectedPosition(({ idx, rowIdx }) => ({
        idx,
        rowIdx,
        mode: 'SELECT',
        rowKey: row?.[rowKey as keyof R] as string | number,
        colKey: column.dataIndex,
      }));
    };

    const onRowChange = (
      row: R,
      commitChanges: boolean,
      shouldFocusCell: boolean,
    ) => {
      if (commitChanges) {
        // Prevents two issues when editor is closed by clicking on a different cell
        //
        // Otherwise commitEditorChanges may be called before the cell state is changed to
        // SELECT and this results in onRowChange getting called twice.
        flushSync(() => {
          updateRow(column, selectedPosition.rowIdx, row);
          closeEditor(shouldFocusCell);
        });
      } else {
        setSelectedPosition((position) => ({ ...position, row }));
      }
    };

    if (rows[selectedPosition.rowIdx] !== selectedPosition.originalRow) {
      // Discard changes if rows are updated from outside
      closeEditor(false);
    }

    return (
      <EditCell
        key={column.key}
        column={column}
        colSpan={colSpan}
        row={row}
        rowIdx={rowIdx}
        onRowChange={onRowChange}
        closeEditor={closeEditor}
        onKeyDown={onCellKeyDown}
        navigate={navigate}
        dataKey={column.dataIndex as keyof R}
        rowSelectionType={rowSelectionType}
        showBorder={showBorder}
        autoRowHeight={autoRowHeight}
        onCellEditFinish={handleCellEditFinish}
      />
    );
  }

  function getRowViewportColumns(rowIdx: number) {
    // idx can be -1 if grouping is enabled
    const selectedColumn =
      selectedPosition.idx === -1 ? undefined : columns[selectedPosition.idx];
    if (
      selectedColumn !== undefined &&
      selectedPosition.rowIdx === rowIdx &&
      !viewportColumns.includes(selectedColumn)
    ) {
      // Add the selected column to viewport columns if the cell is not within the viewport
      return selectedPosition.idx > colOverscanEndIdx
        ? [...viewportColumns, selectedColumn]
        : [
            ...viewportColumns.slice(0, lastLeftFixedColumnIndex + 1),
            selectedColumn,
            ...viewportColumns.slice(lastLeftFixedColumnIndex + 1),
          ];
    }
    return viewportColumns;
  }

  function getViewportRows() {
    const rowElements: React.ReactNode[] = [];

    const { idx: selectedIdx, rowIdx: selectedRowIdx } = selectedPosition;

    const startRowIdx =
      selectedCellIsWithinViewportBounds && selectedRowIdx < rowOverscanStartIdx
        ? rowOverscanStartIdx - 1
        : rowOverscanStartIdx;
    const endRowIdx =
      selectedCellIsWithinViewportBounds && selectedRowIdx > rowOverscanEndIdx
        ? rowOverscanEndIdx + 1
        : rowOverscanEndIdx;

    for (
      let viewportRowIdx = startRowIdx;
      viewportRowIdx <= endRowIdx;
      viewportRowIdx++
    ) {
      const isRowOutsideViewport =
        viewportRowIdx === rowOverscanStartIdx - 1 ||
        viewportRowIdx === rowOverscanEndIdx + 1;
      const rowIdx = isRowOutsideViewport ? selectedRowIdx : viewportRowIdx;

      let rowColumns = viewportColumns;
      const selectedColumn =
        selectedIdx === -1 ? undefined : columns[selectedIdx];
      if (selectedColumn !== undefined) {
        if (isRowOutsideViewport) {
          // if the row is outside the viewport then only render the selected cell
          rowColumns = [selectedColumn];
        } else {
          // if the row is within the viewport and cell is not, add the selected column to viewport columns
          rowColumns = getRowViewportColumns(rowIdx);
        }
      }

      const row = rows[rowIdx];
      const gridRowStart = headerAndTopSummaryRowsCount + rowIdx + 1;
      let key: K | number = rowIdx;
      let isRowSelected = false;
      if (typeof rowKeyGetter === 'function') {
        key = rowKeyGetter(row, rowKeyId);
        isRowSelected = selectedRows?.has(key) ?? false;
      }

      rowElements.push(
        renderRow(key, {
          // aria-rowindex is 1 based
          'aria-rowindex': headerAndTopSummaryRowsCount + rowIdx + 1,
          'aria-selected': isSelectable ? isRowSelected : undefined,
          rowIdx,
          row,
          viewportColumns: rowColumns,
          isRowSelected,
          onCellClick: onCellClickLatest,
          onCellDoubleClick: onCellDoubleClickLatest,
          onCellContextMenu: onContextMenuClick,
          rowClass,
          gridRowStart,
          height: getRowHeight(rowIdx),
          copiedCellIdx:
            copiedCell !== null && copiedCell.row === row
              ? columns.findIndex((c) => c.key === copiedCell.columnKey)
              : undefined,
          selectedCellIdx: selectedRowIdx === rowIdx ? selectedIdx : undefined,
          draggedOverCellIdx: getDraggedOverCellIdx(rowIdx),
          setDraggedOverRowIdx:
            allowGridActions && gridConfig.allowRangeSelection && isDragging
              ? setDraggedOverRowIdx
              : undefined,
          onRowChange: handleFormatterRowChangeLatest,
          selectCell: selectCellLatest,
          selectedCellEditor: getCellEditor(rowIdx),
          rowCount: endRowIdx,
          rowSelectionType,
          lastLeftFixedColumnIndex,
          showBorder,
          autoRowHeight,
          setDragging: setDragging,
          setDraggedOverCellIdx:
            allowGridActions &&
            gridConfig.allowRangeSelection &&
            isDragging &&
            !isDraggingLocked
              ? setDraggedOverCellIdx
              : undefined,
          selectedCellRange: getSelectedCellRange(rowIdx),
          clipboardData: clipboardData,
          latestDraggedOverCellIdx: latestDraggedOverCellIdx,
          latestDraggedOverRowIdx: latestDraggedOverRowIdx,
          selectedRowIdx: selectedRowIdx,
          isDraggingLocked: isDraggingLocked,
          unsetRangeSelection: unsetRangeSelection,
          onDragSerialNoRow: selectSerialNoRow,
          cellSavedStyles: cellStyles as GridCellStyleType[],
          rowKeyId,
          isStickyRowDragRef,
          formulas,
          getParsedRow,
        }),
      );
    }

    return rowElements;
  }

  // Reset the positions if the current values are no longer valid. This can happen if a column or row is removed
  if (selectedPosition.idx > maxColIdx || selectedPosition.rowIdx > maxRowIdx) {
    setSelectedPosition({
      idx: -1,
      rowIdx: minRowIdx - 1,
      mode: 'SELECT',
      rowKey: '',
      colKey: '',
    });
    setDraggedOverRowIdx(undefined);
  }

  let templateRows = `repeat(${headerRowsCount}, ${headerRowHeight}px)`;
  if (topSummaryRowsCount > 0) {
    templateRows += autoRowHeight
      ? ` repeat(${topSummaryRowsCount}, auto)`
      : ` repeat(${topSummaryRowsCount}, ${summaryRowHeight}px)`;
  }

  if (rows.length > 0) {
    if (customGridTemplateRows && customGridTemplateRows?.length > 0) {
      templateRows += customGridTemplateRows;
    } else {
      templateRows += gridTemplateRows;
    }
  }

  if (bottomSummaryRowsCount > 0) {
    templateRows += autoRowHeight
      ? ` repeat(${bottomSummaryRowsCount}, auto)`
      : ` repeat(${bottomSummaryRowsCount}, ${summaryRowHeight}px)`;
  }

  const isGroupRowFocused =
    selectedPosition.idx === -1 && selectedPosition.rowIdx !== minRowIdx - 1;

  const onSortChange = (sortedColumns: SortColumn[]) => {
    if (onSortColumnsChangeLatest) {
      onSortColumnsChangeLatest(sortedColumns);
      saveVersionHistory({
        rows: [...rows],
        columns: [...columns],
        sortColumns: sortedColumns,
        formulas,
        styles: { ...rowColumnStyles, cell: cellStyles },
      });
    }
  };

  return (
    <DataGridProvider value={gridConfig}>
      {allowGridActions && gridConfig.allowEditorToolbar && (
        <EditorToolbar
          rows={rows}
          columns={columns}
          cellSavedStyles={cellStyles as GridCellStyleType[]}
          rowKeyId={rowKeyId}
          selectedPosition={selectedPosition as SelectCellState}
          onStylePropsChange={applyStyleProps}
          canUndo={undoRef.current?.length > 1}
          onUndo={onUndo}
          canRedo={redoRef.current?.length > 0}
          onRedo={onRedo}
          draggedOverCellIdx={draggedOverCellIdx}
          draggedOverRowIdx={draggedOverRowIdx}
          formulas={formulas as GridFormulaType[]}
          onUpdateFormula={updateFormulaChanges}
        />
      )}

      <StyledDataGrid
        id={id}
        role={role}
        aria-label={ariaLabel}
        aria-labelledby={ariaLabelledBy}
        aria-describedby={ariaDescribedBy}
        aria-multiselectable={isSelectable ? true : undefined}
        aria-colcount={columns.length}
        aria-rowcount={ariaRowCount}
        className={clsx(
          rootClassname,
          {
            [viewportDraggingClassname]:
              isDragging && latestDraggedOverRowIdx.current !== undefined,
            editable: allowGridActions,
          },
          className,
        )}
        style={
          {
            ...style,
            // set scrollPadding to correctly position non-sticky cells after scrolling
            scrollPaddingInlineStart:
              selectedPosition.idx > lastLeftFixedColumnIndex ||
              scrollToPosition?.idx !== undefined
                ? `${totalLeftFixedColumnWidth}px`
                : undefined,
            scrollPaddingBlock:
              isRowIdxWithinViewportBounds(selectedPosition.rowIdx) ||
              scrollToPosition?.rowIdx !== undefined
                ? `${
                    headerRowHeight + topSummaryRowsCount * summaryRowHeight
                  }px ${bottomSummaryRowsCount * summaryRowHeight}px`
                : undefined,
            gridTemplateColumns,
            gridTemplateRows: templateRows,
            '--rdg-header-row-height': `${headerRowHeight}px`,
            '--rdg-summary-row-height': `${summaryRowHeight}px`,
            '--rdg-sign': isRtl ? -1 : 1,
            '--rdg-sign-right': isRtl ? 1 : -1,
            ...layoutCssVars,
          } as unknown as React.CSSProperties
        }
        dir={direction}
        ref={gridRef}
        onScroll={handleScroll}
        onKeyDown={handleKeyDown}
        data-testid={testId}
        /*onPaste={handleGridPaste}
        onCopy={() => handleGridCopy()}
        onCut={() => handleGridCopy(handleGridCut)}*/
      >
        <DataGridDefaultRenderersProvider value={defaultGridComponents}>
          <RowSelectionChangeProvider value={selectRowLatest}>
            <RowSelectionProvider value={allRowsSelected}>
              {Array.from(
                { length: groupedColumnHeaderRowsCount },
                (_, index) => (
                  <GroupedColumnHeaderRow
                    key={index}
                    rowIdx={index + 1}
                    level={-groupedColumnHeaderRowsCount + index}
                    columns={getRowViewportColumns(minRowIdx + index)}
                    selectedCellIdx={
                      selectedPosition.rowIdx === minRowIdx + index
                        ? selectedPosition.idx
                        : undefined
                    }
                    selectCell={selectHeaderCellLatest}
                  />
                ),
              )}
              <HeaderRow
                rowIdx={headerRowsCount}
                columns={getRowViewportColumns(mainHeaderRowIdx)}
                onColumnResize={handleColumnResizeLatest}
                onColumnsReorder={onColumnsReorderLatest}
                sortColumns={sortColumns}
                onSortColumnsChange={onSortChange}
                selectedCellIdx={
                  selectedPosition.rowIdx === mainHeaderRowIdx
                    ? selectedPosition.idx
                    : undefined
                }
                selectCell={selectHeaderCellLatest}
                shouldFocusGrid={!selectedCellIsWithinSelectionBounds}
                direction={direction}
                rowSelectionType={rowSelectionType}
                filters={filters}
                onFiltersChange={onFiltersChangeLatest}
                lastLeftFixedColumnIndex={lastLeftFixedColumnIndex}
                showBorder={showBorder}
                onInsertCell={onInsertCell}
                onDeleteCells={onDeleteCells}
                onRenameColumn={onRenameColumn}
                onLocalFiltersChange={onLocalFiltersChangeLatest}
                saveVersionHistory={saveVersionHistory}
                rowCount={rows.length}
                onSerialNoRowHeaderClick={selectSerialNoRow}
                selectedPosition={selectedPosition as SelectCellState}
                draggedOverCellIdx={draggedOverCellIdx as number}
              />
            </RowSelectionProvider>
            {rows.length === 0 && noRowsFallback ? (
              noRowsFallback
            ) : (
              <>
                {topSummaryRows?.map((row, rowIdx) => {
                  const gridRowStart = headerRowsCount + 1 + rowIdx;
                  const summaryRowIdx = mainHeaderRowIdx + 1 + rowIdx;
                  const isSummaryRowSelected =
                    selectedPosition.rowIdx === summaryRowIdx;
                  const top = headerRowsHeight + summaryRowHeight * rowIdx;

                  return (
                    <SummaryRow
                      key={rowIdx}
                      aria-rowindex={gridRowStart}
                      rowIdx={summaryRowIdx}
                      gridRowStart={gridRowStart}
                      row={row}
                      top={top}
                      bottom={undefined}
                      viewportColumns={getRowViewportColumns(summaryRowIdx)}
                      selectedCellIdx={
                        isSummaryRowSelected ? selectedPosition.idx : undefined
                      }
                      isTop
                      selectCell={selectCellLatest}
                      lastLeftFixedColumnIndex={lastLeftFixedColumnIndex}
                      showBorder={rowIdx === topSummaryRowsCount - 1}
                      rowKeyId={rowKeyId}
                    />
                  );
                })}
                {getViewportRows()}
                {bottomSummaryRows?.map((row, rowIdx) => {
                  const gridRowStart =
                    headerAndTopSummaryRowsCount + rows.length + rowIdx + 1;
                  const summaryRowIdx = rows.length + rowIdx;
                  const isSummaryRowSelected =
                    selectedPosition.rowIdx === summaryRowIdx;
                  const top =
                    clientHeight > totalRowHeight
                      ? gridHeight -
                        summaryRowHeight *
                          ((bottomSummaryRows?.length || 0) - rowIdx)
                      : undefined;
                  const bottom =
                    top === undefined
                      ? summaryRowHeight *
                        ((bottomSummaryRows?.length || 0) - 1 - rowIdx)
                      : undefined;

                  return (
                    <SummaryRow
                      aria-rowindex={
                        ariaRowCount - bottomSummaryRowsCount + rowIdx + 1
                      }
                      key={rowIdx}
                      rowIdx={summaryRowIdx}
                      gridRowStart={gridRowStart}
                      row={row}
                      top={top}
                      bottom={bottom}
                      viewportColumns={getRowViewportColumns(summaryRowIdx)}
                      selectedCellIdx={
                        isSummaryRowSelected ? selectedPosition.idx : undefined
                      }
                      isTop={false}
                      selectCell={selectCellLatest}
                      lastLeftFixedColumnIndex={lastLeftFixedColumnIndex}
                      showBorder={rowIdx === 0}
                      rowKeyId={rowKeyId}
                    />
                  );
                })}
              </>
            )}
          </RowSelectionChangeProvider>
        </DataGridDefaultRenderersProvider>

        {renderDragHandle()}

        {/* render empty cells that span only 1 column so we can safely measure column widths, regardless of colSpan */}
        {renderMeasuringCells(viewportColumns)}

        {/* extra div is needed for row navigation in a treegrid */}
        {isTreeGrid && (
          <StyledTreeGridWrapper
            ref={focusSinkRef}
            tabIndex={isGroupRowFocused ? 0 : -1}
            className={clsx('focus-sink', {
              'focus-sink-header-summary': !isRowIdxWithinViewportBounds(
                selectedPosition.rowIdx,
              ),
              'row-selected': isGroupRowFocused,
              'row-selected-frozen':
                isGroupRowFocused && lastLeftFixedColumnIndex !== -1,
            })}
            style={{
              gridRowStart:
                selectedPosition.rowIdx + headerAndTopSummaryRowsCount + 1,
            }}
          />
        )}

        {scrollToPosition !== null && (
          <ScrollToCell
            scrollToPosition={scrollToPosition}
            setScrollToCellPosition={setScrollToPosition}
            gridElement={gridRef.current!}
          />
        )}
      </StyledDataGrid>
      {/*<StyledScrollbar style={{ bottom: hidePagination ? 0 : 72 }}>
          <SimpleBar
            ref={scrollRef}
            scrollableNodeProps={{ ref: scrollableNodeRef }}
          >
            <div
              className='scrollbar-content'
              style={{ width: gridRef?.current?.scrollWidth }}
            />
          </SimpleBar>
        </StyledScrollbar>*/}

      {allowGridActions && (
        <Fragment>
          {gridConfig.allowRangeSelection && gridConfig.allowCountFooter && (
            <FooterRow
              selectedPosition={selectedPosition as SelectCellState}
              draggedOverCellIdx={draggedOverCellIdx!}
              draggedOverRowIdx={draggedOverRowIdx!}
              rows={rows}
              columns={columns}
            />
          )}

          {gridConfig.allowContextMenu && (
            <ContextWindow
              onCloseModal={onCloseContextModal}
              selectedPosition={selectedPosition as SelectCellState}
              draggedOverCellIdx={draggedOverCellIdx!}
              draggedOverRowIdx={draggedOverRowIdx!}
              rows={rows}
              columns={columns}
              onInsertRows={onInsertRows}
              onDeleteRows={onDeleteRows}
              onInsertCell={onInsertCell}
              onDeleteCells={onDeleteCells}
              canUndo={undoRef.current?.length > 1}
              onUndo={onUndo}
              canRedo={redoRef.current?.length > 0}
              onRedo={onRedo}
              onCut={() => handleGridCopy(handleGridCut)}
              onCopy={() => handleGridCopy()}
              onPaste={() => handleGridPaste()}
              open={openContextMenu}
              saveVersionHistory={saveVersionHistory}
            />
          )}

          {gridConfig.allowFindReplace && findReplaceModalOpen && (
            <FindAndReplace
              open={findReplaceModalOpen}
              findString={findString}
              onClose={() => {
                setFindReplaceModalOpen(false);
                setFindString('');
              }}
              rows={rows}
              columns={columns}
              setSelectedPosition={(position) => {
                setSelectedPosition(position);
                setDraggedOverCellIdx(undefined);
                setDraggedOverRowIdx(undefined);
              }}
              setScrollToPosition={setScrollToPosition}
              onRowsChange={onRowsChange}
              rowKeyId={rowKeyId}
            />
          )}

          {gridConfig.allowFindRecord && (
            <FindRecord
              isOpen={openFindBox}
              setFindString={setFindString}
              rows={rows}
              columns={columns}
              setSelectedPosition={(position) => {
                setSelectedPosition(position);
                setDraggedOverCellIdx(undefined);
                setDraggedOverRowIdx(undefined);
              }}
              setScrollToPosition={setScrollToPosition}
              onMoreOptionsClick={() => {
                setFindReplaceModalOpen(true);
                setOpenFindBox(false);
              }}
              onClose={() => setOpenFindBox(false)}
              rowKeyId={rowKeyId}
            />
          )}
        </Fragment>
      )}
    </DataGridProvider>
  );
}

function getCellToScroll(gridEl: HTMLDivElement) {
  return gridEl.querySelector<HTMLDivElement>(
    ':scope > [role="row"] > [tabindex="0"]',
  );
}

function isSamePosition(p1: Position, p2: Position) {
  return p1.idx === p2.idx && p1.rowIdx === p2.rowIdx;
}

export default forwardRef(DataGrid) as <R, SR = unknown, K extends Key = Key>(
  props: DataGridProps<R, SR, K> & RefAttributes<DataGridHandle>,
) => JSX.Element;
