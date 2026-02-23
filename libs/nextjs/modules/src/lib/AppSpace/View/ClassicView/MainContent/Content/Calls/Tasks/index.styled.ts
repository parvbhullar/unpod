import styled from 'styled-components';
import {Avatar, Flex, Typography} from 'antd';
import {lighten} from 'polished';

const {Text} = Typography;

export const StyledRoot = styled.div`
  background-color: ${({theme}) => theme.palette.background.default};
  height: calc(100vh - 130px);
  overflow-y: auto;
  scrollbar-width: thin;
`;

export const StyledDocumentsList = styled.div`
  width: 100%;
  max-width: calc(${({theme}) => theme.sizes.mainContentWidth});
  background-color: ${({theme}) => theme.palette.background.default};
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  border-radius: 12px 12px 0 0;

  @media (max-width: ${({theme}) => theme.breakpoints.xl}px) {
    padding: 14px;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    padding: 8px 10px;
  }
`;

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
`;

export const StyledFlex = styled(Flex)`
  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    gap: 4px !important;
  }
`;

export const StyledListItemContent = styled.div`
  display: flex;
  flex-direction: column;
`;
