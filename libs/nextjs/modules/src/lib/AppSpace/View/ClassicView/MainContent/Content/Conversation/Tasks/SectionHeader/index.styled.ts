import styled from 'styled-components';
import { Flex, Typography } from 'antd';

const { Text } = Typography;

export const StyledTaskCount = styled(Text)`
  background: ${({ theme }) => theme.palette.background.component};
  padding: 4px 12px;
  border-radius: ${({ theme }) => theme.radius.base}px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    border-radius: ${({ theme }) => theme.radius.base + 6}px;
    padding: 5px 10px;
    font-size: 10px;
  }
`;

export const StyledFlex = styled(Flex)`
  border-bottom: 1px ${({ theme }) => theme.border.style}
    ${({ theme }) => theme.border.color};
  padding-bottom: 12px;
`;
