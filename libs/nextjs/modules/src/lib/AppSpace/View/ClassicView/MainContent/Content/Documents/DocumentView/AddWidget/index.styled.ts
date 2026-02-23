import styled from 'styled-components';

export const StyledRoot = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 74px);
  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    padding: 12px;
  }
`;

export const StyledItemRoot = styled('div')`
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  background-color: ${({theme}) => theme.palette.background.default};
  border: 1px solid ${({theme}) => theme.border.color};
  border-radius: 16px;
  cursor: pointer;
  max-width: 400px;
  margin: 0 auto;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: ${({theme}) => theme.palette.background.component};
  }
`;

export const StyledContent = styled('div')`
  margin: 0;
`;

export const StyledTitleWrapper = styled('div')`
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 12px;

  & .ant-typography {
    margin: 0 !important;
  }
`;
