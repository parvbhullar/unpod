import styled from 'styled-components';
import { Flex } from 'antd';

export const StyledRoot = styled.div`
  margin: 24px 0 0 0;

  .ant-col {
    width: 100% !important;
  }
`;

export const StyledFlex = styled(Flex)`
  width: 100%;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column !important;
    margin-bottom: 24px;
    gap: 0 !important;
  }
`;
