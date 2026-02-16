import styled from 'styled-components';

export const StyledRoot = styled.div`
  font-family: ${({ theme }) => theme.font.family};
  color: ${({ theme }) => theme.palette.text.primary};

  /* Light theme. */
  --color-canvas-default: #ffffff;
  --color-canvas-subtle: #f6f8fa;
  --color-border-default: #d0d7de;
  --color-border-muted: hsla(210, 18%, 87%, 1);

  /* Dark theme. */
  @media (prefers-color-scheme: dark) {
    --color-canvas-default: #0d1117;
    --color-canvas-subtle: #161b22;
    --color-border-default: #30363d;
    --color-border-muted: #21262d;
  }

  & ol,
  & ul,
  & dl {
    margin: 0;
    padding: 0 0 12px 30px;
  }

  table {
    border-spacing: 0;
    border-collapse: collapse;
    display: block;
    margin-top: 0;
    margin-bottom: 16px;
    //width: max-content;
    width: fit-content;
    max-width: 100%;
    overflow: auto;
  }

  tr {
    background-color: var(--color-canvas-default);
    border-top: 1px solid var(--color-border-muted);
  }

  tr:nth-child(2n) {
    background-color: var(--color-canvas-subtle);
  }

  td,
  th {
    padding: 6px 13px;
    border: 1px solid var(--color-border-default);
  }

  th {
    font-weight: 600;
  }

  table img {
    background-color: transparent;
  }
`;

export const StyledCopyWrapper = styled.div`
  position: absolute;
  top: 8px;
  right: 8px;
  bottom: auto;
  left: auto;
  z-index: 1;
  opacity: 0;
  transition: opacity 0.3s;
`;

export const StyledContainer = styled.div`
  position: relative;

  &:hover ${StyledCopyWrapper} {
    opacity: 1;
  }
`;
