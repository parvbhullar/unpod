import styled from 'styled-components';

export const StyledRoot = styled('div')`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
`;

export const StyledContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); /* 'auto-fill' को 'auto-fit' से बदल सकते हैं */
  align-items: center;
  gap: 12px;
  width: 60%;
  margin: 0 auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 100%;
  }
`;

export const StyledItemRoot = styled('div')`
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  background-color: ${({ theme }) => theme.palette.background.default};
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: 16px;
  cursor: pointer;
  max-width: 100%;
  height: 100%;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: ${({ theme }) => theme.palette.background.component};
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
