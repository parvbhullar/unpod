import styled from 'styled-components';

export const StyledListContainer = styled.ul`
  padding: 0;
  margin: 0;
`;

export const StyledListItem = styled.li`
  list-style: none;
  font-size: ${({ theme }) => theme.font.size.base};
  background-color: ${({ theme }) => theme.palette.background.default};
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: ${({ theme }) =>
    `${theme.border.width} ${theme.border.style} ${theme.border.color}`};
  cursor: pointer;
  transition: background-color 0.2s ease-in-out;

  &:hover,
  &:focus {
    background-color: ${({ theme }) => theme.palette.primary}33;
  }

  &:last-child {
    border-bottom: none;
  }
`;

export const StyledHeadingItem = styled(StyledListItem)`
  font-weight: ${({ theme }) => theme.font.weight.semiBold};
  border-bottom: none;
  margin-top: 5px;

  &:hover,
  &:focus {
    background-color: transparent;
  }
`;

export const RemoveMenuItem = styled(StyledListItem)`
  color: ${({ theme }) => theme.palette.error};
`;
