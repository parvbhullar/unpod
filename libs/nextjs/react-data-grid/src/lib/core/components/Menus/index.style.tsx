import styled from 'styled-components';
import { rgba } from 'polished';

export const StyledMenu = styled.menu`
  padding: 10px 0;
  margin: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 80vh;
  min-width: 220px;
  overflow-y: auto;
`;

export const StyledMenuItem = styled.li`
  display: flex;
  align-items: center;
  gap: 8px;
  color: ${({ theme }: { theme: any }) =>
    theme.text?.heading ?? theme.palette?.text?.primary ?? '#111'};
  padding: 7px 10px;
  // border-radius: 8px;
  width: 100%;
  cursor: pointer;
  transition: background-color 0.3s ease;

  &.disabled {
    color: ${({ theme }: { theme: any }) =>
      theme.text?.disabled ?? theme.palette?.text?.disabled ?? '#888'};
    pointer-events: none;
  }

  & > span {
    flex: 1;
    display: inline-flex;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
  }

  &:hover {
    background-color: ${({ theme }) => rgba(theme.palette.primary, 0.15)};
  }
`;
