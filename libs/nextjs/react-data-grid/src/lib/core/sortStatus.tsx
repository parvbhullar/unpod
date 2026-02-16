import styled from 'styled-components';

import type {
  RenderSortIconProps,
  RenderSortPriorityProps,
  RenderSortStatusProps,
} from './models/data-grid';

const StyledSorters = styled.span`
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  padding-bottom: 3px;

  &:hover {
    svg {
      fill: rgba(0, 0, 0, 0.59) !important;
    }
  }
`;

const StyledSorterTop = styled.span<{ fillColor: string }>`
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  color: inherit;
  font-style: normal;
  line-height: 0;
  text-align: center;
  text-transform: none;
  vertical-align: -0.125em;
  text-rendering: optimizeLegibility;

  svg {
    fill: ${({ fillColor }: { fillColor: string }) =>
      fillColor !== ''
        ? fillColor
        : ({ theme }: { theme: any }) => theme.table.headerIconColor};
  }
`;

const StyledSorterBottom = styled(StyledSorterTop)`
  margin-top: -0.3em;
`;

export default function renderSortStatus({
  sortDirection,
  priority,
}: RenderSortStatusProps) {
  return (
    <>
      {renderSortIcon({ sortDirection })}
      {renderSortPriority({ priority })}
    </>
  );
}

function Sorter({ sortDirection }: { sortDirection?: string }) {
  return (
    <StyledSorters aria-hidden="true">
      <StyledSorterTop
        role="img"
        aria-label="caret-up"
        fillColor={sortDirection === 'ASC' ? '#182a88' : ''}
      >
        <svg
          viewBox="0 0 1024 1024"
          focusable="false"
          data-icon="caret-up"
          width="1em"
          height="1em"
          aria-hidden="true"
        >
          <path d="M858.9 689L530.5 308.2c-9.4-10.9-27.5-10.9-37 0L165.1 689c-12.2 14.2-1.2 35 18.5 35h656.8c19.7 0 30.7-20.8 18.5-35z" />
        </svg>
      </StyledSorterTop>
      <StyledSorterBottom
        role="img"
        aria-label="caret-down"
        fillColor={
          sortDirection === 'ASC'
            ? ''
            : sortDirection === 'DESC'
              ? '#182a88'
              : ''
        }
      >
        <svg
          viewBox="0 0 1024 1024"
          focusable="false"
          data-icon="caret-down"
          width="1em"
          height="1em"
          aria-hidden="true"
        >
          <path d="M840.4 300H183.6c-19.7 0-30.7 20.8-18.5 35l328.4 380.8c9.4 10.9 27.5 10.9 37 0L858.9 335c12.2-14.2 1.2-35-18.5-35z" />
        </svg>
      </StyledSorterBottom>
    </StyledSorters>
  );
}

export function renderSortIcon({ sortDirection }: RenderSortIconProps) {
  if (sortDirection === undefined) return <Sorter />;

  return <Sorter sortDirection={sortDirection} />;
}

export function renderSortPriority({ priority }: RenderSortPriorityProps) {
  return priority;
}
