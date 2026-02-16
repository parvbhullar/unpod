import { memo } from 'react';
import styled from 'styled-components';
import clsx from 'clsx';

import { getColSpan, getRowStyle } from './utils';
import type { RenderRowProps } from './models/data-grid';
import { CellFrozen, StyledCellWrapper } from './style/cell';
import {
  rowClassname,
  rowSelectedClassname,
  StyledRowWrapper,
} from './style/row';
import SummaryCell from './SummaryCell';

type SharedRenderRowProps<R, SR> = Pick<
  RenderRowProps<R, SR>,
  'viewportColumns' | 'rowIdx' | 'gridRowStart' | 'selectCell'
>;

type SummaryRowProps<R, SR> = SharedRenderRowProps<R, SR> & {
  'aria-rowindex': number;
  row: SR;
  top: number | undefined;
  bottom: number | undefined;
  lastLeftFixedColumnIndex: number;
  selectedCellIdx: number | undefined;
  isTop: boolean;
  showBorder: boolean;
  rowKeyId: string;};

const StyledSummaryRow = styled(StyledRowWrapper)`
  &.rdg-summary-row {
    line-height: var(--rdg-summary-row-height);

    > ${StyledCellWrapper} {
      position: sticky;
    }
  }

  &.rdg-top-summary-row {
    > ${StyledCellWrapper} {
      z-index: 2;
    }

    > ${CellFrozen} {
      z-index: 3;
    }
  }
  &.top-summary-row-border {
    > ${StyledCellWrapper} {
      border-block-end: 2px solid
        ${({ theme }: { theme: any }) => theme.table.borderColor};
    }
  }
  &.bottom-summary-row-border {
    > ${StyledCellWrapper} {
      border-block-start: 2px solid
        ${({ theme }: { theme: any }) => theme.table.borderColor};
    }
  }
`;

function SummaryRow<R, SR>({
  rowIdx,
  gridRowStart,
  row,
  viewportColumns,
  top,
  bottom,
  selectedCellIdx,
  isTop,
  selectCell,
  'aria-rowindex': ariaRowIndex,
  lastLeftFixedColumnIndex,
  showBorder,
  rowKeyId,
}: SummaryRowProps<R, SR>) {
  const cells = [];
  for (let index = 0; index < viewportColumns.length; index++) {
    const column = viewportColumns[index];
    const colSpan = getColSpan(column, lastLeftFixedColumnIndex, {
      type: 'SUMMARY',
      row,
    });
    if (colSpan !== undefined) {
      index += colSpan - 1;
    }

    const isCellSelected = selectedCellIdx === column.idx;

    cells.push(
      <SummaryCell<R, SR>
        key={column.key ?? column.dataIndex}
        column={column}
        colSpan={colSpan}
        row={row}
        rowIdx={rowIdx}
        isCellSelected={isCellSelected}
        selectCell={selectCell}
        rowKeyId={rowKeyId}
      />,
    );
  }

  return (
    <StyledSummaryRow
      role="row"
      aria-rowindex={ariaRowIndex}
      className={clsx(
        rowClassname,
        `rdg-row-${rowIdx % 2 === 0 ? 'even' : 'odd'}`,
        'rdg-summary-row',
        {
          [rowSelectedClassname]: selectedCellIdx === -1,
          'rdg-top-summary-row': isTop,
          'top-summary-row-border': isTop && showBorder,
          'bottom-summary-row-border': !isTop && showBorder,
          'rdg-bottom-summary-row': !isTop,
        },
      )}
      style={
        {
          ...getRowStyle(gridRowStart),
          '--rdg-summary-row-top': top !== undefined ? `${top}px` : undefined,
          '--rdg-summary-row-bottom':
            bottom !== undefined ? `${bottom}px` : undefined,
        } as unknown as React.CSSProperties
      }
    >
      {cells}
    </StyledSummaryRow>
  );
}

export default memo(SummaryRow) as <R, SR>(
  props: SummaryRowProps<R, SR>,
) => JSX.Element;
