import styled from 'styled-components';

export const StyledContainer = styled.div`
  width: 100%;
  max-width: calc(100% - 88px);
  margin: 0 0 0 44px;
  padding: 0 20px;
`;

export const StyledSourceList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0;
  /*background-color: ${({theme}) => theme.palette.background.default};
  border-radius: ${({theme}) => theme.component.card.borderRadius};
  box-shadow: ${({theme}) => theme.component.card.boxShadow};*/
  overflow: hidden;
  margin: 0;
  list-style: none;
`;

export const StyledContent = styled.div`
  display: flex;
  align-items: center;
  // justify-content: space-between;
  gap: 16px;
  padding: 16px;
  background-color: ${({theme}) => theme.palette.background.default};
  cursor: pointer;
  transition: background-color 0.3s;
`;

export const StyledListItem = styled.li`
  font-size: 16px;
  margin: 0;
  padding: 0;

  &:hover ${StyledContent} {
    background-color: ${({theme}) => theme.palette.background.component};
  }
`;
