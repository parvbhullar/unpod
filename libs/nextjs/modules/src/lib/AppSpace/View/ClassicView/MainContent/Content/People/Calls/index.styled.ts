import styled from 'styled-components';
import {Avatar, Flex, Typography} from 'antd';
import {lighten} from 'polished';

const {Text} = Typography;

export const StyledAvatar = styled(Avatar)`
  background-color: ${({theme}) => theme.palette.background.component};
  color: ${({theme}) => theme.palette.text.secondary};

  &.success {
    color: ${({theme}) => theme.palette.common.white};
    background: ${({theme}) => lighten(0.2, theme.palette.success)};
  }
  &.error {
    color: ${({theme}) => theme.palette.common.white};
    background: ${({theme}) => lighten(0.2, theme.palette.error)};
  }
`;

export const StyledText = styled(Text)`
  font-size: 12px;
  white-space: nowrap;
`;

export const StyledDot = styled.div`
  width: 4px;
  height: 4px;
  background: ${({theme}) => theme.palette.text.secondary};
  border-radius: 50%;

  @media (min-width: ${({theme}) =>
  theme.breakpoints.md + 1}px) and (max-width: ${({theme}) =>
  theme.breakpoints.xl - 1}px) {
    display: none;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    display: none;
  }
`;

export const StyledFlex = styled(Flex)`
  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    gap: 4px !important;
  }
`;

export const StyledFlexItem = styled(Flex)`
  gap: 8px;

  @media (min-width: ${({theme}) =>
  theme.breakpoints.md + 1}px) and (max-width: ${({theme}) =>
  theme.breakpoints.xl - 1}px) {
    flex-direction: column;
    gap: 8px;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    flex-direction: column;
  }
`;

export const StyledHeaderTitle = styled.div`
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid ${({theme}) => theme.border.color};

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    gap: 6px;
  }
`;
