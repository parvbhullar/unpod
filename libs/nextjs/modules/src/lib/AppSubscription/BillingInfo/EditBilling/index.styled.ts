import styled from 'styled-components';
import { Flex } from 'antd';

export const StyledContainer = styled.div`
  margin-top: 16px;
  display: flex;
  max-width: ${({ theme }) => theme.sizes.mainContentWidth};
  flex-direction: column;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    max-width: 100%;
  }
`;

export const StyledButtonWrapper = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
`;

export const StyledItemRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
`;

export const StyledFlex = styled(Flex)`
  justify-content: flex-end;

  @media (max-width: ${({ theme }) => theme.breakpoints.xss}px) {
    width: 100%;
    justify-content: space-between;
  }
`;
