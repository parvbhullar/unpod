import styled from 'styled-components';
import { Avatar, Flex, Segmented, Typography } from 'antd';

const { Text } = Typography;

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  height: calc(100vh - 130px);
  overflow-y: auto;
  scrollbar-width: thin;
`;

export const StyledContainer = styled.div`
  padding: 16px 32px;
  margin: 0 auto;
  width: 100%;
  max-width: calc(${({ theme }) => theme.sizes.mainContentWidth});
  background-color: ${({ theme }) => theme.palette.background.default};
  display: flex;
  flex-direction: column;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 6px 8px;
  }
`;

export const StyledSegmentSticky = styled.div`
  position: sticky;
  top: 0;
  z-index: 10;
  background: ${({ theme }) => theme.palette.background.default};
`;

export const StyledDocumentsList = styled.div`
  padding: 16px 32px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 6px 8px;
  }
`;

export const StyledAvatar = styled(Avatar)`
  color: ${({ theme }) => theme.palette.common.white};

  &.failed {
    background-color: ${({ theme }) => theme.palette.error};
  }

  &.completed {
    background-color: ${({ theme }) => theme.palette.success};
  }

  &.upcoming {
    background-color: ${({ theme }) => theme.palette.info};
  }
`;

export const StyledSegmented = styled(Segmented)`
  position: sticky;
  top: 0;
  z-index: 1;
  background: ${({ theme }) => theme.palette.background.default};
  border-radius: 0;
  width: 100%;
  padding: 12px 32px;
  border-bottom: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};

  .ant-segmented-group {
    gap: ${({ theme }) => theme.space.md};
  }

  .ant-segmented-item {
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: ${({ theme }) => theme.space.xs};
    white-space: nowrap;
    border: none;
    box-shadow: none;
    border-radius: ${({ theme }) => theme.radius.base + 8}px;

    &:hover {
      background: ${({ theme }) => theme.palette.primaryHover};
      color: ${({ theme }) => theme.palette.text.heading};
    }
  }

  .ant-segmented-item-selected {
    background: ${({ theme }) => theme.palette.primaryHover};
    color: ${({ theme }) => theme.palette.text.heading};
  }
`;

export const StyledTabsContent = styled.div`
  display: flex;
  gap: 8px;
  align-items: center;
  text-align: center;
  padding: 2px 12px;
`;

export const StyledFlex = styled(Flex)`
  ${({ theme }) => theme.border.color};
  padding: 14px 0;
  width: 100%;

  &:last-child {
    padding-bottom: 0;
  }
`;

export const StyledDescription = styled(Text)`
  line-height: 1.5 !important;
  font-size: 12px !important;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    line-height: 1.3 !important;
  }
`;

export const StyledText = styled(Text)`
  text-decoration: line-through;
  color: ${({ theme }) => theme.palette.text.secondary};
`;
