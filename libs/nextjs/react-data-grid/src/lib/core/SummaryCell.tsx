import { memo } from 'react';
import styled from 'styled-components';

import { useRovingTabIndex } from './hooks';
import { getCellClassname, getCellStyle } from './utils';
import type { CellRendererProps } from './models/data-grid';
import { StyledCellWrapper } from './style/cell';

export const StyledSummaryCell = styled(StyledCellWrapper)`
  &.summary-cell {
    inset-block-start: var(--rdg-summary-row-top);
    inset-block-end: var(--rdg-summary-row-bottom);
  }
`;

type SharedCellRendererProps<R, SR> = Pick<
  CellRendererProps<R, SR>,
  'rowIdx' | 'column' | 'colSpan' | 'isCellSelected' | 'selectCell'
>;

type SummaryCellProps<R, SR> = SharedCellRendererProps<R, SR> & {
  row: SR;
  rowKeyId: string;};

function SummaryCell<R, SR>({
  column,
  colSpan,
  row,
  rowIdx,
  isCellSelected,
  selectCell,
  rowKeyId,
}: SummaryCellProps<R, SR>) {
  const { tabIndex, childTabIndex, onFocus } =
    useRovingTabIndex(isCellSelected);
  const { summaryCellClass } = column;
  const className = getCellClassname(
    column,
    'summary-cell',
    typeof summaryCellClass === 'function'
      ? summaryCellClass(row)
      : summaryCellClass,
  );

  function onClick() {
    selectCell({
      rowIdx,
      idx: column.idx,
      rowKey: row?.[rowKeyId as keyof SR] as string | number,
      colKey: column.dataIndex,
    });
  }

  return (
    <StyledSummaryCell
      role="gridcell"
      aria-colindex={column.idx + 1}
      aria-colspan={colSpan}
      aria-selected={isCellSelected}
      tabIndex={tabIndex}
      className={className}
      style={getCellStyle(column, colSpan)}
      onClick={onClick}
      onFocus={onFocus}
    >
      {column.renderSummaryCell?.({ column, row, tabIndex: childTabIndex })}
    </StyledSummaryCell>
  );
}

export default memo(SummaryCell) as <R, SR>(
  props: SummaryCellProps<R, SR>,
) => JSX.Element;
