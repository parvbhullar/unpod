import type * as React from 'react';
import type { Key, ReactElement, ReactNode } from 'react';
import type { Dayjs } from 'dayjs';
import type { PopoverProps, TablePaginationConfig } from 'antd';

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

type DefaultColumnOptions<R, SR> = Pick<
  Column<R, SR>,
  'renderCell' | 'width' | 'minWidth' | 'maxWidth' | 'resizable' | 'sorter'
>;

export type AppTableProps = {
  columns: any[];
  dataSource: any[];
  loading?: boolean;
  isLoadingMore?: boolean;
  isDraggable?: boolean;
  fullHeight?: boolean;
  id?: string;
  scroll?: any;
  rowKey?: string;
  className?: string;
  onChange?: any;
  size?: 'small' | 'middle' | 'large';
  bordered?: boolean;
  rowSelection?: TableRowSelection<any>;
  pagination?: TablePaginationConfig | false;
  onRowDragEnd?: (data: any[]) => void;
  customBlockSize?: number;

  customRowHeight?: Maybe<number | ((row: any) => number)>;
  defaultColumnOptions?: Maybe<DefaultColumnOptions<any, any>>;
  extraHeight?: number;
  hasLocalFilters?: boolean;
  themeOptions?: themeOptions;
  onScrolledToBottom?: () => void;
  [x: string]: any;};

export type DataGridProps<R, SR = unknown, K extends Key = Key> = SharedDivProps & {
  /**
   * Grid and data Props
   */
  /** An array of objects representing each column on the grid */
  columns: readonly Column<R, SR>[];
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

  /**
   * Dimensions props
   */
  /**
   * The height of each row in pixels
   * @default 35
   */
  rowHeight?: Maybe<number | ((row: R) => number)>;
  border?: Maybe<boolean>;
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
  filters?: FilterType;
  onFiltersChange?: Maybe<
    Maybe<React.Dispatch<React.SetStateAction<FilterType>>>
  >;
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
  /** Called when the grid is scrolled */
  onScroll?: Maybe<(event: React.UIEvent<HTMLDivElement>) => void>;
  /** Called when a column is resized */
  onColumnResize?: Maybe<(idx: number, width: number) => void>;

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
  'data-testid'?: Maybe<string>;};

export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;

export type Maybe<T> = T | undefined | null;

export type StateSetter<S> = React.Dispatch<React.SetStateAction<S>>;
export type ColumnType = Maybe<string | number | boolean | Date>;
export type FilterDataType = Maybe<string[] | [Dayjs | null, Dayjs | null]>;

export type Column<TRow, TSummaryRow = unknown> = {
  /** The name of the column. By default it will be displayed in the header cell */
  readonly title: string | ReactElement;
  /** A unique key to distinguish each column */
  readonly key?: string;
  readonly dataIndex: string;
  readonly dataType?: string;
  readonly headerCellOptions?: boolean;

  /** Column width. If not specified, it will be determined automatically based on grid width and specified widths of other columns */
  readonly width?: Maybe<number | string>;
  /** Minimum column width in px. */
  readonly minWidth?: Maybe<number>;
  /** Maximum column width in px. */
  readonly maxWidth?: Maybe<number>;
  readonly cellClass?: Maybe<string | ((row: TRow) => Maybe<string>)>;
  readonly headerCellClass?: Maybe<string>;
  readonly summaryCellClass?: Maybe<
    string | ((row: TSummaryRow) => Maybe<string>)
  >;
  /** Render function used to render the content of the column's header cell */
  readonly renderHeaderCell?: Maybe<
    (props: RenderHeaderCellProps<TRow, TSummaryRow>) => ReactNode
  >;
  readonly sorter?: Maybe<
    (a: TRow, b: TRow, key: keyof TRow, type?: string) => number
  >;
  readonly filterIcon?: Maybe<(filtered: boolean) => JSX.Element>;
  readonly filterDropdown?: (props: FilterDropdownProps) => React.ReactNode;

  readonly filters?: ColumnFilterItem[];

  /** Render function used to render the content of cells */
  readonly render?: Maybe<
    (value: any, props: TRow, tabIndex: number) => ReactNode
  >;
  readonly renderCell?: Maybe<
    (props: RenderCellProps<TRow, TSummaryRow>) => ReactNode
  >;
  /** Render function used to render the content of summary cells */
  readonly renderSummaryCell?: Maybe<
    (props: RenderSummaryCellProps<TSummaryRow, TRow>) => ReactNode
  >;
  /** Render function used to render the content of group cells */
  readonly renderGroupCell?: Maybe<
    (props: RenderGroupCellProps<TRow, TSummaryRow>) => ReactNode
  >;
  /** Render function used to render the content of edit cells. When set, the column is automatically set to be editable */
  readonly renderEditCell?: Maybe<
    (props: RenderEditCellProps<TRow, TSummaryRow>) => ReactNode
  >;
  /** Enables cell editing. If set and no editor property specified, then a textinput will be used as the cell editor */
  readonly editable?: Maybe<boolean | ((row: TRow) => boolean)>;
  readonly colSpan?: Maybe<
    (args: ColSpanArgs<TRow, TSummaryRow>) => Maybe<number>
  >;
  readonly rowSpan?: Maybe<
    (params: RowSpanArgs<TRow, TSummaryRow>) => Maybe<number>
  >;
  /** Determines whether column is frozen or not */
  readonly frozen?: Maybe<boolean>;
  readonly fixed?: string;
  /** Enable resizing of a column */
  readonly resizable?: Maybe<boolean>;
  /** Enable sorting of a column */
  readonly sortable?: Maybe<boolean>;
  /** Enable dragging of a column */
  readonly draggable?: Maybe<boolean>;
  /** Sets the column sort order to be descending instead of ascending the first time the column is sorted */
  readonly sortDescendingFirst?: Maybe<boolean>;
  readonly editorOptions?: Maybe<{
    /**
     * Render the cell content in addition to the edit cell.
     * Enable this option when the editor is rendered outside the grid, like a modal for example.
     * By default, the cell content is not rendered when the edit cell is open.
     * @default false
     */
    readonly displayCellContent?: Maybe<boolean>;
    /** @default true */
    readonly commitOnOutsideClick?: Maybe<boolean>;
  }>;};

export type ColumnsType<S, R = unknown> = (Column<S, R> | ColumnGroup<S, R>)[];

type AlignType = 'left' | 'right' | 'center';

export type CalculatedColumn<TRow, TSummaryRow = unknown> = Column<
  TRow,
  TSummaryRow
> & {
  readonly parent: CalculatedColumnParent<TRow, TSummaryRow> | undefined;
  readonly idx: number;
  readonly alphaIdx: string;
  readonly level: number;
  readonly width: number | string;
  readonly minWidth: number;
  readonly maxWidth: number | undefined;
  readonly resizable: boolean;
  readonly sortable: boolean;
  readonly frozen: boolean;
  readonly fixed?: string;
  readonly align?: Maybe<AlignType>;
  readonly isLastFrozenColumn: boolean;
  readonly isFirstRightFixedColumn: boolean;
  readonly isFirstFrozenColumn?: boolean;
  readonly renderCell: (props: RenderCellProps<TRow, TSummaryRow>) => ReactNode;};

export type ColumnGroup<R, SR = unknown> = {
  /** The name of the column group, it will be displayed in the header cell */
  readonly title: string | ReactElement;
  readonly key?: string;
  readonly dataIndex?: string;
  readonly headerCellClass?: Maybe<string>;
  readonly children: readonly ColumnOrColumnGroup<R, SR>[];};

export type CalculatedColumnParent<R, SR> = {
  readonly title: string | ReactElement;
  readonly parent: CalculatedColumnParent<R, SR> | undefined;
  readonly idx: number;
  readonly colSpan: number;
  readonly level: number;
  readonly align?: Maybe<AlignType>;
  readonly headerCellClass?: Maybe<string>;};

export type ColumnOrColumnGroup<R, SR = unknown> =
  | Column<R, SR>
  | ColumnGroup<R, SR>;

export type CalculatedColumnOrColumnGroup<R, SR> =
  | CalculatedColumnParent<R, SR>
  | CalculatedColumn<R, SR>;

export type Position = {
  readonly idx: number;
  readonly rowIdx: number;};
export type CellPosition = Position & {
  rowKey: number | string;
  colKey: string;};

export type RenderCellProps<TRow, TSummaryRow = unknown> = {
  column: CalculatedColumn<TRow, TSummaryRow>;
  row: TRow;
  isCellEditable: boolean;
  tabIndex: number;
  onRowChange: (row: TRow) => void;
  rowSelectionType: 'radio' | 'checkbox';};

export type RenderSummaryCellProps<TSummaryRow, TRow = unknown> = {
  column: CalculatedColumn<TRow, TSummaryRow>;
  row: TSummaryRow;
  tabIndex: number;};

export type RenderGroupCellProps<TRow, TSummaryRow = unknown> = {
  groupKey: unknown;
  column: CalculatedColumn<TRow, TSummaryRow>;
  row: GroupRow<TRow>;
  childRows: readonly TRow[];
  isExpanded: boolean;
  tabIndex: number;
  toggleGroup: () => void;
  rowSelectionType?: 'radio' | 'checkbox';};

export type RenderEditCellProps<TRow, TSummaryRow = unknown> = {
  column: CalculatedColumn<TRow, TSummaryRow>;
  row: TRow;
  onRowChange: (row: TRow, commitChanges?: boolean) => void;
  onClose: (commitChanges?: boolean, shouldFocusCell?: boolean) => void;};

export type RenderEditSelectCellProps<TRow, TSummaryRow = unknown> = RenderEditCellProps<TRow, TSummaryRow> & {
  options: readonly any[];};

export type RenderHeaderCellProps<TRow, TSummaryRow = unknown> = {
  column: CalculatedColumn<TRow, TSummaryRow>;
  sortDirection: SortDirection | undefined;
  priority: number | undefined;
  tabIndex: number;

  filterValue: FilterDataType | undefined;
  onFilter: (key: string, value: FilterDataType) => void;
  onSort: (ctrlClick: boolean) => void;
  rowSelectionType?: 'radio' | 'checkbox';
  headerColumnOptions?: ReactNode;
  onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;};

export type CellRendererProps<TRow, TSummaryRow> = Pick<RenderRowProps<TRow, TSummaryRow>, 'row' | 'rowIdx' | 'selectCell'> & Omit<
      React.HTMLAttributes<HTMLDivElement>,
      'style' | 'children' | 'onClick' | 'onDoubleClick' | 'onContextMenu'
    > & {
  column: CalculatedColumn<TRow, TSummaryRow>;
  colSpan: number | undefined;
  isCopied: boolean;
  isDraggedOver: boolean;
  isCellSelected: boolean;
  onClick: RenderRowProps<TRow, TSummaryRow>['onCellClick'];
  onDoubleClick: RenderRowProps<TRow, TSummaryRow>['onCellDoubleClick'];
  onContextMenu: RenderRowProps<TRow, TSummaryRow>['onCellContextMenu'];
  onRowChange: (
    column: CalculatedColumn<TRow, TSummaryRow>,
    newRow: TRow,
  ) => void;
  rowSelectionType: 'radio' | 'checkbox';
  // Author Gaurav Kumar
  showBorder: boolean;
  // Author Babulal Kumawat
  autoRowHeight?: boolean;
  setDragging: React.Dispatch<React.SetStateAction<boolean>>;
  setDraggedOverCellIdx:
    | ((overCellIdx: number | undefined) => void)
    | undefined;
  latestDraggedOverCellIdx: React.MutableRefObject<number | undefined>;
  latestDraggedOverRowIdx: React.MutableRefObject<number | undefined>;
  unsetRangeSelection: () => void;
  isLeftSelectedCell?: boolean;
  isRightSelectedCell?: boolean;
  isTopSelectedCell?: boolean;
  isBottomSelectedCell?: boolean;
  idx: number;
  isLeftCopiedCell?: boolean;
  isRightCopiedCell?: boolean;
  isTopCopiedCell?: boolean;
  isBottomCopiedCell?: boolean;
  isPartiallySelected?: boolean;
  onDragSerialNoRow: (cellIdx?: number, rowIdx?: number) => void;
  isStickyRowDragRef: React.MutableRefObject<boolean>;
  columnCount: number;
  getParsedRow: (row: TRow, dataIndex: keyof TRow, formula?: string) => TRow;
  formulas?: GridFormulaType[];
  cellSavedStyles?: GridCellStyleType[];
  rowKeyId: string;};

export type CellEvent<E extends React.SyntheticEvent<HTMLDivElement>> = E & {
  preventGridDefault: () => void;
  isGridDefaultPrevented: () => boolean;
};

export type CellMouseEvent = CellEvent<React.MouseEvent<HTMLDivElement>>;

export type CellKeyboardEvent = CellEvent<React.KeyboardEvent<HTMLDivElement>>;

export type CellClickArgs<TRow, TSummaryRow = unknown> = {
  row: TRow;
  column: CalculatedColumn<TRow, TSummaryRow>;
  selectCell: (enableEditor?: boolean) => void;};

type SelectCellKeyDownArgs<TRow, TSummaryRow = unknown> = {
  mode: 'SELECT';
  row: TRow;
  column: CalculatedColumn<TRow, TSummaryRow>;
  rowIdx: number;
  selectCell: (position: Position, enableEditor?: Maybe<boolean>) => void;};

export type EditCellKeyDownArgs<TRow, TSummaryRow = unknown> = {
  mode: 'EDIT';
  row: TRow;
  column: CalculatedColumn<TRow, TSummaryRow>;
  rowIdx: number;
  navigate: () => void;
  onClose: (commitChanges?: boolean, shouldFocusCell?: boolean) => void;};

export type CellKeyDownArgs<TRow, TSummaryRow = unknown> =
  | SelectCellKeyDownArgs<TRow, TSummaryRow>
  | EditCellKeyDownArgs<TRow, TSummaryRow>;

export type CellSelectArgs<TRow, TSummaryRow = unknown> = {
  rowIdx: number;
  row: TRow;
  column: CalculatedColumn<TRow, TSummaryRow>;};

export type BaseRenderRowProps<TRow, TSummaryRow = unknown> = Omit<React.HTMLAttributes<HTMLDivElement>, 'style' | 'children'> & Pick<
      DataGridProps<TRow, TSummaryRow>,
      'onCellClick' | 'onCellDoubleClick' | 'onCellContextMenu'
    > & {
  viewportColumns: readonly CalculatedColumn<TRow, TSummaryRow>[];
  rowIdx: number;
  selectedCellIdx: number | undefined;
  isRowSelected: boolean;
  gridRowStart: number;
  height: number;
  selectCell: (position: CellPosition, enableEditor?: Maybe<boolean>) => void;
  onDragSerialNoRow: (cellIdx?: number, rowIdx?: number) => void;};

export type RenderRowProps<TRow, TSummaryRow = unknown> = BaseRenderRowProps<TRow, TSummaryRow> & {
  row: TRow;
  showBorder: boolean;
  rowCount: number;
  copiedCellIdx: number | undefined;
  draggedOverCellIdx: number | undefined;
  selectedCellEditor: ReactElement<RenderEditCellProps<TRow>> | undefined;
  onRowChange: (
    column: CalculatedColumn<TRow, TSummaryRow>,
    rowIdx: number,
    newRow: TRow,
  ) => void;
  rowClass: Maybe<(row: TRow, rowIdx: number) => Maybe<string>>;
  setDraggedOverRowIdx: ((overRowIdx: number | undefined) => void) | undefined;
  lastLeftFixedColumnIndex: number;
  rowSelectionType: 'radio' | 'checkbox';
  // Author Babulal Kumawat
  autoRowHeight?: boolean;
  setDragging: React.Dispatch<React.SetStateAction<boolean>>;
  setDraggedOverCellIdx:
    | ((overCellIdx: number | undefined) => void)
    | undefined;
  selectedCellRange: [number, number] | undefined;
  clipboardData: CopyClipboardProps | null;
  latestDraggedOverCellIdx: React.MutableRefObject<number | undefined>;
  latestDraggedOverRowIdx: React.MutableRefObject<number | undefined>;
  selectedRowIdx: number;
  isDraggingLocked?: boolean;
  unsetRangeSelection: () => void;
  isStickyRowDragRef: React.MutableRefObject<boolean>;
  getParsedRow: (row: TRow, dataIndex: keyof TRow, formula?: string) => TRow;
  formulas?: GridFormulaType[];
  cellSavedStyles?: GridCellStyleType[];
  rowKeyId: string;};

export type RowsChangeData<R, SR = unknown> = {
  indexes: number[];
  column: CalculatedColumn<R, SR>;};

export type CopyClipboardProps = {
  startIdx: number;
  startRowIdx: number;
  endIdx: number;
  endRowIdx: number;
  content: string;
};

export type SelectRowEvent<TRow> =
  | { type: 'HEADER'; checked: boolean }
  | { type: 'ROW'; row: TRow; checked: boolean; isShiftClick: boolean };

export type RowSpanArgs<R, SR> =
  | {
      type: 'ROW';
      row: R;
    }
  | {
      type: 'SUMMARY';
      row: SR;
    };

export type FillEvent<TRow> = {
  columnKey: string;
  sourceRow: TRow;
  targetRow: TRow;};

export type CopyEvent<TRow> = {
  sourceColumnKey: string;
  sourceRow: TRow;};

export type PasteEvent<TRow> = {
  sourceColumnKey: string;
  sourceRow: TRow;
  targetColumnKey: string;
  targetRow: TRow;};

export type GroupRow<TRow> = {
  readonly childRows: readonly TRow[];
  readonly id: string;
  readonly parentId: unknown;
  readonly groupKey: unknown;
  readonly isExpanded: boolean;
  readonly level: number;
  readonly posInSet: number;
  readonly setSize: number;
  readonly startRowIndex: number;};

export type SortColumn = {
  readonly columnKey: string;
  readonly direction: SortDirection;};

export type FilterType = Record<string, FilterDataType>;

type AcceptedInputType = string | number | boolean | Date | null | undefined;
export type AcceptedObjectInputType = {
  start: AcceptedInputType;
  end: AcceptedInputType;
};

export type LocalFilter = {
  columnKey: string;
  operator: string;
  inputVal: AcceptedInputType | AcceptedObjectInputType;
  dataType?: string;
};

export type GridFormulaType = {
  rowKey: number | string;
  colKey: number | string;
  formula: string | null;
};

export type GridRowColStyleType = {
  rows: { [x: number | string]: React.CSSProperties | null };
  columns: { [x: number | string]: React.CSSProperties | null };
};

export type GridCellStyleType = {
  rowKey: number | string;
  colKey: number | string;
  style: React.CSSProperties | null;
};

export type ColumnStyleType = {
  [x: string | number]: React.CSSProperties | null;
};

export type CellNavigationMode = 'NONE' | 'CHANGE_ROW';
export type SortDirection = 'ASC' | 'DESC';

export type ColSpanArgs<TRow, TSummaryRow> =
  | { type: 'HEADER' }
  | { type: 'ROW'; row: TRow }
  | { type: 'SUMMARY'; row: TSummaryRow };

export type RowHeightArgs<TRow> =
  | { type: 'ROW'; row: TRow }
  | { type: 'GROUP'; row: GroupRow<TRow> };

export type RenderSortIconProps = {
  sortDirection: SortDirection | undefined;};

export type RenderSortPriorityProps = {
  priority: number | undefined;};

export type RenderSortStatusProps = RenderSortIconProps & RenderSortPriorityProps & {};

export type RenderCheckboxProps = Pick<
  React.InputHTMLAttributes<HTMLInputElement>,
  | 'aria-label'
  | 'aria-labelledby'
  | 'checked'
  | 'tabIndex'
  | 'disabled'
  | 'type'
> & {
  onChange: (checked: boolean, shift: boolean) => void;};

export type Renderers<TRow, TSummaryRow> = {
  renderCheckbox?: Maybe<(props: RenderCheckboxProps) => JSX.Element>;
  renderRow?: Maybe<
    (key: Key, props: RenderRowProps<TRow, TSummaryRow>) => ReactNode
  >;
  renderSortStatus?: Maybe<(props: RenderSortStatusProps) => ReactNode>;
  noRowsFallback?: Maybe<ReactNode>;};

export type Direction = 'ltr' | 'rtl';

export type FilterConfirmProps = {
  closeDropdown: boolean;};

export type ColumnFilterItem = {
  text: React.ReactNode;
  value: string | number | boolean;
  children?: ColumnFilterItem[];};

export type FilterDropdownProps = {
  prefixCls?: string;
  setSelectedKeys: (keys: FilterDataType) => void;
  selectedKeys: FilterDataType;
  /**
   * Confirm filter value, if you want to close dropdown before commit, you can call with
   * {closeDropdown: true}
   */
  confirm: () => void;
  clearFilters?: () => void;
  filters?: ColumnFilterItem[];
  /** Only close filterDropdown */
  close?: () => void;
  visible?: boolean;};

export type RowSelectionType = 'checkbox' | 'radio';

export type TableRowSelection<T> = {
  type?: RowSelectionType;
  selectedRowKeys: Key[];
  onChange: (selectedRowKeys: Key[], selectedRows: T[]) => void;};

export type ConfirmWindowProps = {
  title?: string;
  message?: string;
  onConfirm: () => void;
  onCancel?: () => void;
  canBtnText?: string;
  confBtnText?: string;
};

export type MenuItemProps = {
  label: ReactNode | string;
  icon: ReactNode | string;
  onClick?: (event: React.MouseEvent<HTMLLIElement>) => void;
  confirmWindowProps?: PopoverProps & ConfirmWindowProps;
  disabled?: boolean;
};

export type UndoRedoProcessProps = {
  rows: any[];
  columns: any[];
  sortColumns: SortColumn[];
  formulas?: GridFormulaType[];
  styles?: {
    rows?: { [x: number | string]: React.CSSProperties | null };
    columns?: { [x: number | string]: React.CSSProperties | null };
    cell?: GridCellStyleType[];
  };};

export type TableCellItemProps = {
  idx: number;
  title: string;
  column_key: string;
};

export type ContextMenuProps = {
  allowCopy?: boolean;
  allowCut?: boolean;
  allowPaste?: boolean;
  allowUndo?: boolean;
  allowRedo?: boolean;
  allowInsertRows?: boolean;
  allowDeleteRows?: boolean;
  allowAddColumns?: boolean;
  allowDeleteColumns?: boolean;
};

export type HeaderMenuProps = {
  allowSorting?: boolean;
  allowAddColumn?: boolean;
  allowRenameColumn?: boolean;
  allowDeleteColumn?: boolean;
  allowFilter?: boolean;
};

export type EditorToolbarProps = {
  allowBold?: boolean;
  allowItalic?: boolean;
  allowUnderline?: boolean;
  allowStrikeThrough?: boolean;
  allowFillColor?: boolean;
  allowTextColor?: boolean;
  allowUndo?: boolean;
  allowRedo?: boolean;
  allowFormula?: boolean;
  allowFormulaInput?: boolean;
};

export type GridConfiguration = {
  allowGridActions?: boolean;
  showSerialNoRow?: boolean;
  allowRangeSelection?: boolean;
  allowEditCell?: boolean;
  allowUndoRedo?: boolean;
  allowFormula?: boolean;
  allowFindReplace?: boolean;
  allowFindRecord?: boolean;
  allowContextMenu: true;
  allowEditorToolbar?: boolean;
  allowCountFooter?: boolean;
  allowCellAlphaName?: boolean;
  contextMenu: ContextMenuProps;
  headerMenu: HeaderMenuProps;
  editorToolbar: EditorToolbarProps;
};

export type MediaBreakpoints = {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  xxl: number;
};

export type themeOptions = {
  font?: {
    size?: {
      base?: string;
      lg?: string;
      sm?: string;
      xl?: string;
    };
    weight?: {
      light?: number;
      regular?: number;
      medium?: number;
      semiBold?: number;
      bold?: number;
    };
  };
  text?: {
    heading?: string;
    primary?: string;
    secondary?: string;
    disabled?: string;
    placeholder?: string;
    hint?: string;
  };
  border?: {
    color?: string;
    width?: string;
    radius?: string;
    inputBorderColor?: string;
  };
  table?: {
    textColor?: string;
    outlineColor?: string;
    borderColor?: string;
    borderHoverColor?: string;
    activeBorderColor?: string;
    selectedHoverColor?: string;
    headerBgColor?: string;
    rowOverBgColor?: string;
    headerIconColor?: string;
  };
  primaryColor?: string;
  backgroundColor?: string;
  copiedBgColor?: string;
  errorColor?: string;
  breakpoints?: MediaBreakpoints;
  direction?: string;
};

declare const AppInputField: <TRow, TSummaryRow>({
  row,
  column,
  onRowChange,
  onClose,
}: RenderEditCellProps<TRow, TSummaryRow>) => JSX.Element;

export declare const SelectInput: <TRow, TSummaryRow>({
  row,
  column,
  onRowChange,
  onClose,
  options,
}: RenderEditSelectCellProps<TRow, TSummaryRow>) => JSX.Element;

export declare const TimeInput: typeof AppInputField;
export declare const DateInput: typeof AppInputField;
export declare const NumberEditor: typeof AppInputField;
export declare const TextEditor: typeof AppInputField;
export declare const DateTimeInput: typeof AppInputField;
export declare const AppDataGrid: (props: AppTableProps) => JSX.Element;
