import styled from 'styled-components';

export const StyledMenuItem = styled.span`
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

export const StyledIconWrapper = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px;
  background-color: ${({theme}) => theme.palette.primary}33;
  border: 1px solid ${({theme}) => theme.palette.primary}77;
  border-radius: 12px;
  color: ${({theme}) => theme.palette.primary}99 !important;
`;

export const StyledSubMenuItem = styled.span`
  display: flex;
  align-items: center;

  &.add-new-title {
    color: ${({theme}) => theme.palette.primary};
  }

  & > svg {
    min-width: 16px;
  }
`;

export const StyledSubMenuText = styled.span`
  margin-left: 10px;
  display: inline-block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;
