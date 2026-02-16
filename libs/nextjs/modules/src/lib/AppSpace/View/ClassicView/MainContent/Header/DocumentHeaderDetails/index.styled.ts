import styled from 'styled-components';
import { Badge, Flex, Typography } from 'antd';

const { Text } = Typography;

export const StyledHeaderSubtitle = styled(Text)`
  font-size: 11px !important;
  color: ${({ theme }) => theme.palette.text.secondary};
  margin: 0;
  max-width: 600px;
  line-height: 1 !important;
`;

export const StyledEmailText = styled(Text)`
  font-size: 12px !important;
  color: ${({ theme }) => theme.palette.text.secondary};
  margin: 0;
  max-width: 600px;
  line-height: 1 !important;
`;

export const StyledBadge = styled(Badge)`
  display: inline-block;
  font-size: 11px;
  padding: 4px 10px;
  background-color: ${({ theme }) => theme.palette.warning};
  color: ${({ theme }) => theme.palette.common.white};
  border-radius: 5px;
  min-width: 0;

  &.success {
    background: ${({ theme }) => theme.palette.success};
  }
  &.Enterprise {
    background: ${({ theme }) => theme.palette.background.component};
    color: ${({ theme }) => theme.palette.common.black} !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    border-radius: 4px;
    font-size: 10px;
    padding: 2px 4px;
  }
`;

export const StyledFlexContainer = styled(Flex)`
  width: 100%;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;

  @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    gap: 2px !important;
  }
`;

export const StyledFlex = styled(Flex)`
  align-items: center;

  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    align-items: flex-start;
    gap: 0 !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    align-items: flex-start;
    flex-direction: column;
    gap: 0 !important;
  }
`;

export const StyledEmailContainer = styled(Flex)`
  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    display: none;
  }
`;
