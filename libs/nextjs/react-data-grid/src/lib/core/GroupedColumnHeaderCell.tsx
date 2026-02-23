import clsx from 'clsx';

import {useRovingTabIndex} from './hooks';
import {getHeaderCellRowSpan, getHeaderCellStyle} from './utils';
import type {CalculatedColumnParent} from './models/data-grid';
import {type GroupedColumnHeaderRowProps} from './GroupedColumnHeaderRow';
import {cellClassname} from './style/cell';
import styled from 'styled-components';

const StyledGroupCell = styled.div`
  color: ${({theme}: { theme: any }) => theme.table.textColor};
  background: ${({theme}: { theme: any }) => theme.table.headerBgColor};
  border-bottom: 1px solid;
  border-right: 1px solid;
  border-color: ${({theme}: { theme: any }) => theme.table.borderColor};

  &.rdg-cell {
    position: sticky;
    z-index: 2;
    border-radius: 0 !important;
  }
`;

type SharedGroupedColumnHeaderRowProps<R, SR> = Pick<
  GroupedColumnHeaderRowProps<R, SR>,
  'rowIdx' | 'selectCell'
>;

type GroupedColumnHeaderCellProps<R, SR> = SharedGroupedColumnHeaderRowProps<R, SR> & {
  column: CalculatedColumnParent<R, SR>;
  isCellSelected: boolean;
};

export default function GroupedColumnHeaderCell<R, SR>({
                                                         column,
                                                         rowIdx,
                                                         isCellSelected,
                                                         selectCell,
                                                       }: GroupedColumnHeaderCellProps<R, SR>) {
  const {tabIndex, onFocus} = useRovingTabIndex(isCellSelected);
  const {colSpan} = column;
  const rowSpan = getHeaderCellRowSpan(column, rowIdx);
  const index = column.idx + 1;

  function onClick() {
    selectCell({idx: column.idx, rowIdx});
  }

  return (
    <StyledGroupCell
      role="columnheader"
      aria-colindex={index}
      aria-colspan={colSpan}
      aria-rowspan={rowSpan}
      aria-selected={isCellSelected}
      tabIndex={tabIndex}
      className={clsx(cellClassname, column.headerCellClass)}
      style={{
        ...getHeaderCellStyle(column, rowIdx, rowSpan),
        gridColumnStart: index,
        textAlign: column.align ?? 'center',
        gridColumnEnd: index + colSpan,
      }}
      onFocus={onFocus}
      onClick={onClick}
    >
      {column.title}
    </StyledGroupCell>
  );
}
