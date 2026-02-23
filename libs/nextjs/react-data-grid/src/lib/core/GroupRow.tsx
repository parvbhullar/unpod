import {memo} from 'react';
import styled from 'styled-components';
import clsx from 'clsx';

import {RowSelectionProvider} from './hooks';
import {getRowStyle} from './utils';
import type {BaseRenderRowProps, GroupRow} from './models/data-grid';
import {SELECT_COLUMN_KEY} from './constants/AppConst';
import GroupCell from './GroupCell';
import {CellFrozenLast, StyledCellWrapper} from './style/cell';
import {rowClassname, rowSelectedClassname, StyledRowWrapper,} from './style/row';

const StyledGroupRow = styled(StyledRowWrapper)`
  > ${StyledCellWrapper}:not(:last-child):not(${CellFrozenLast}) {
    border-inline-end: none;
  }
`;

type GroupRowRendererProps<R, SR> = BaseRenderRowProps<R, SR> & {
  row: GroupRow<R>;
  groupBy: readonly string[];
  toggleGroup: (expandedGroupId: unknown) => void;
  rowKeyId: string;
};

function GroupedRow<R, SR>({
                             className,
                             row,
                             rowIdx,
                             viewportColumns,
                             selectedCellIdx,
                             isRowSelected,
                             selectCell,
                             gridRowStart,
                             height,
                             groupBy,
                             toggleGroup,
                             rowKeyId,
                             ...props
                           }: GroupRowRendererProps<R, SR>) {
  // Select is always the first column
  const idx =
    viewportColumns[0].key === SELECT_COLUMN_KEY ? row.level + 1 : row.level;

  function handleSelectGroup() {
    selectCell({
      rowIdx,
      idx: -1,
      rowKey: row?.[rowKeyId as keyof GroupRow<R>] as string | number,
      colKey: '',
    });
  }

  return (
    <RowSelectionProvider value={isRowSelected}>
      <StyledGroupRow
        role="row"
        aria-level={row.level + 1} // aria-level is 1-based
        aria-setsize={row.setSize}
        aria-posinset={row.posInSet + 1} // aria-posinset is 1-based
        aria-expanded={row.isExpanded}
        className={clsx(
          rowClassname,
          'rdg-group-row',
          `rdg-row-${rowIdx % 2 === 0 ? 'even' : 'odd'}`,
          selectedCellIdx === -1 && rowSelectedClassname,
          className,
        )}
        onClick={handleSelectGroup}
        style={getRowStyle(gridRowStart, height)}
        {...props}
      >
        {viewportColumns.map((column) => (
          <GroupCell
            key={column.dataIndex}
            id={row.id}
            groupKey={row.groupKey}
            childRows={row.childRows}
            isExpanded={row.isExpanded}
            isCellSelected={selectedCellIdx === column.idx}
            column={column}
            row={row}
            groupColumnIndex={idx}
            toggleGroup={toggleGroup}
            isGroupByColumn={groupBy.includes(column.dataIndex)}
          />
        ))}
      </StyledGroupRow>
    </RowSelectionProvider>
  );
}

export default memo(GroupedRow) as <R, SR>(
  props: GroupRowRendererProps<R, SR>,
) => JSX.Element;
