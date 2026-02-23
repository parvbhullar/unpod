import styled from 'styled-components';

export const StyledMenu = styled.menu`
  padding: 0;
  margin: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 260px;
  min-width: 220px;
  overflow-y: auto;
  scrollbar-width: thin;
`;

export const StyledMenuItem = styled.li`
  display: flex;
  align-items: center;
  gap: 8px;
  color: ${({theme}) => theme.palette.text.primary};
  padding: 7px 10px;
  width: 100%;
  cursor: pointer;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: ${({theme}) => theme.palette.primaryHover};
  }

  &.active {
    background-color: ${({theme}) => theme.palette.primaryHover};
    color: ${({theme}) => theme.palette.primary};
  }

  &.disabled {
    color: ${({theme}) => theme.palette.text.secondary};
    background-color: ${({theme}) => theme.palette.background.disabled};
    cursor: not-allowed;

    &:hover,
    &.active {
      background-color: ${({theme}) => theme.palette.background.disabled};
    }
  }

  & .menu-label {
    flex: 1;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
`;
