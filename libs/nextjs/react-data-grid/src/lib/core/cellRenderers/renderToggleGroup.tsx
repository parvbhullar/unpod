import React from 'react';
import styled from 'styled-components';
import type {RenderGroupCellProps} from '../models/data-grid';

const StyledGroupCellContent = styled.span`
  outline: none;
`;

const StyledCaret = styled.svg`
  margin-inline-start: 4px;
  stroke: currentColor;
  stroke-width: 1.5px;
  fill: transparent;
  vertical-align: middle;

  > path {
    transition: d 0.1s;
  }
`;

export function renderToggleGroup<R, SR>(props: RenderGroupCellProps<R, SR>) {
  return <ToggleGroup {...props} />;
}

export function ToggleGroup<R, SR>({
                                     groupKey,
                                     isExpanded,
                                     tabIndex,
                                     toggleGroup,
                                   }: RenderGroupCellProps<R, SR>) {
  function handleKeyDown({key}: React.KeyboardEvent<HTMLSpanElement>) {
    if (key === 'Enter') {
      toggleGroup();
    }
  }

  const d = isExpanded ? 'M1 1 L 7 7 L 13 1' : 'M1 7 L 7 1 L 13 7';

  return (
    <StyledGroupCellContent
      className="rdg-group-cell-content"
      tabIndex={tabIndex}
      onKeyDown={handleKeyDown}
    >
      {groupKey as string}
      <StyledCaret
        viewBox="0 0 14 8"
        width="14"
        height="8"
        className="rdg-caret"
        aria-hidden
      >
        <path d={d}/>
      </StyledCaret>
    </StyledGroupCellContent>
  );
}
