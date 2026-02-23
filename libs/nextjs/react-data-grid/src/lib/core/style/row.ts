import styled from 'styled-components';

export const StyledRowWrapper = styled.div`
  display: contents;
  // line-height: var(--rdg-row-height);
  min-height: var(--rdg-row-height);

  &.row-dragging {
    opacity: 0.5;
  }

  &.row-over {
    background: ${({theme}: { theme: any }) => theme.table.rowOverBgColor};
  }

  /*&.last-row {
    .rdg-cell {
      border-block-end: none !important;
    }
  }*/

  &:hover {
    .rdg-cell {
      background: ${({theme}: { theme: any }) => theme.palette.primaryHover};
    }
  }

  &[aria-selected='true'] {
    .rdg-cell {
      background: ${({theme}: { theme: any }) => theme.palette.primaryActive};
    }

    &:hover {
      .rdg-cell {
        background: ${({theme}: { theme: any }) =>
  theme.palette.primaryActiveHover};
      }
    }
  }
`;

export const rowClassname = 'rdg-row';

export const rowHidden = 'rdg-hidden';

export const rowSelectedClassname = 'rdg-row-selected';
