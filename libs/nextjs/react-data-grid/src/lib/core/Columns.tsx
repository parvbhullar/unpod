import {useRowSelection} from './hooks';
import type {Column, RenderCellProps, RenderGroupCellProps, RenderHeaderCellProps,} from './models/data-grid';
import {SelectCellFormatter} from './cellRenderers';
import {SELECT_COLUMN_KEY} from './constants/AppConst';

function HeaderRenderer(props: RenderHeaderCellProps<unknown>) {
  const [isRowSelected, onRowSelectionChange] = useRowSelection();

  return (
    <SelectCellFormatter
      aria-label="Select All"
      tabIndex={props.tabIndex}
      type={props.rowSelectionType ?? 'checkbox'}
      value={isRowSelected}
      onChange={(checked) => {
        onRowSelectionChange({type: 'HEADER', checked});
      }}
    />
  );
}

function SelectFormatter(props: RenderCellProps<unknown>) {
  const [isRowSelected, onRowSelectionChange] = useRowSelection();

  return (
    <SelectCellFormatter
      aria-label="Select"
      tabIndex={props.tabIndex}
      value={isRowSelected}
      type={props.rowSelectionType ?? 'checkbox'}
      onChange={(checked, isShiftClick) => {
        onRowSelectionChange({
          type: 'ROW',
          row: props.row,
          checked,
          isShiftClick,
        });
      }}
    />
  );
}

function SelectGroupFormatter(props: RenderGroupCellProps<unknown>) {
  const [isRowSelected, onRowSelectionChange] = useRowSelection();

  return (
    <SelectCellFormatter
      aria-label="Select Group"
      tabIndex={props.tabIndex}
      value={isRowSelected}
      type={props.rowSelectionType ?? 'checkbox'}
      onChange={(checked) => {
        onRowSelectionChange({
          type: 'ROW',
          row: props.row,
          checked,
          isShiftClick: false,
        });
      }}
    />
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const SelectColumn: Column<any, any> = {
  title: '',
  dataIndex: SELECT_COLUMN_KEY,
  key: SELECT_COLUMN_KEY,
  width: 33,
  minWidth: 33,
  maxWidth: 33,
  resizable: false,
  // sortable: false,
  // frozen: true,
  fixed: 'left',
  renderHeaderCell(props) {
    return <HeaderRenderer {...props} />;
  },
  renderCell(props) {
    return <SelectFormatter {...props} />;
  },
  renderGroupCell(props) {
    return <SelectGroupFormatter {...props} />;
  },
};
