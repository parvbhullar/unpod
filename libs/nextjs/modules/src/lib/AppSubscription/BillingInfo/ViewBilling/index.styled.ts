import { Flex } from 'antd';
import styled from 'styled-components';

export const StyledGridContainer = styled.div`
  margin-top: 16px;
  display: flex;
  width: 100%;
  max-width: ${({ theme }) => theme.sizes.mainContentWidth};
  flex-direction: column;
  gap: 12px;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    max-width: 100%;
  }
`;

export const StyledItemWrapper = styled.div`
  display: flex;
  flex-direction: column;
`;

export const StyledFlex = styled(Flex)`
  margin-top: 24px;
`;
