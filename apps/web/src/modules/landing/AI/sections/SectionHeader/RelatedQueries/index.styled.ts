import styled from 'styled-components';

export const StyledContainer = styled.div`
  position: relative;
  height: 100%;
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 60px auto 16px auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    margin: 16px auto 16px auto;
  }
`;

export const StyledTitle = styled.div`
  padding: 16px 0;
  white-space: nowrap;
  font-size: 18px;
  font-weight: 600;
  text-align: center;
`;

export const StyledSourceList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0;
  background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
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
  background-color: ${({ theme }) => theme.palette.background.default};
  transition: background-color 0.3s;
`;

export const StyledListItem = styled.li`
  font-size: 16px;
  margin: 0;
  padding: 0;
  cursor: pointer;

  &:hover ${StyledContent} {
    background-color: ${({ theme }) => theme.palette.background.component};
  }
`;
