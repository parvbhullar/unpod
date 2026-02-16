import { Flex } from 'antd';
import styled from 'styled-components';

export const StyledFlex = styled(Flex)`
  gap: 50px;
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    gap: 10px;
  }
`;
