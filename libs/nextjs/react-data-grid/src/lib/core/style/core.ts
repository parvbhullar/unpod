import styled from 'styled-components';

import {StyledRowWrapper} from './row';

export const StyledDataGrid = styled.div`
  *,
  *::before,
  *::after {
    box-sizing: inherit;
  }
  display: grid;
  contain: content;
  content-visibility: auto;
  block-size: 350px;
  border: 1px solid ${({theme}: { theme: any }) => theme.table.borderColor};
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  box-sizing: border-box;
  overflow-x: auto;
  overflow-y: auto;
  background-color: ${({theme}: { theme: any }) => theme.backgroundColor};
  padding-bottom: 10px;
  margin-bottom: -10px;

  /* needed on Firefox */
  &::before {
    content: '';
    grid-column: 1/-1;
    grid-row: 1/-1;
  }

  &::-webkit-scrollbar,
  & *::-webkit-scrollbar {
    width: 7px;
    height: 7px;
  }

  &::-webkit-scrollbar-track,
  & *::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb,
  & *::-webkit-scrollbar-thumb {
    background: rgba(127, 127, 127, 0.8);
    border-radius: 10px;
  }

  &.viewport-dragging {
    user-select: none;

    & ${StyledRowWrapper} {
      cursor: move;
    }
  }

  &.editable {
    user-select: none;
  }
`;

export const rootClassname = 'rdg';

export const viewportDraggingClassname =
  'rdg-viewport-dragging viewport-dragging';

export const StyledTreeGridWrapper = styled.div`
  &.focus-sink {
    grid-column: 1/-1;
    pointer-events: none;
    /* Should have a higher value than 1 to show up above regular frozen cells */
    z-index: 1;
  }

  &.focus-sink-header-summary {
    /* Should have a higher value than 3 to show up above header and summary rows */
    z-index: 3;
  }

  &.row-selected {
    outline: 2px solid ${({theme}: { theme: any }) => theme.table.selectedHoverColor};
    outline-offset: -2px;
  }

  &.row-selected-frozen {
    &::before {
      content: '';
      display: inline-block;
      height: 100%;
      position: sticky;
      inset-inline-start: 0;
      border-inline-start: 2px solid ${({theme}: { theme: any }) => theme.table.selectedHoverColor};
    }
  }
`;

export const StyledScrollbar = styled.div`
  overflow-x: auto;
  overflow-y: hidden;
  position: sticky;
  bottom: 72px;
  border: 1px solid transparent;

  & .scrollbar-content {
    height: 10px;
  }
`;
