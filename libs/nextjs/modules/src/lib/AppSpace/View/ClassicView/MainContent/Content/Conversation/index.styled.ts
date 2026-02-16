import { Segmented } from 'antd';
import styled from 'styled-components';

export const StyledWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
`;

export const StyledScrollArea = styled.div`
  flex: 1;
  overflow-x: auto;
  display: flex;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  padding: 12px 32px;
  max-width: calc(${({ theme }) => theme.sizes.mainContentWidth}) !important;
  flex-direction: column;
  align-items: flex-start;
  margin: 0 auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 12px 0 12px 8px !important;
  }

  &::-webkit-scrollbar {
    display: none;
  }
`;

export const StyledSegmented = styled(Segmented)`
  background: ${({ theme }) => theme.palette.background.default};
  padding: 0;
  border-radius: 0 !important;

  .ant-segmented-group {
    display: flex;
    flex-wrap: nowrap;
    overflow: hidden;
    gap: 8px;
  }

  .ant-segmented-item {
    font-size: 13px;
    font-weight: 500;
    color: ${({ theme }) => theme.palette.text.secondary};
    background: ${({ theme }) => theme.palette.background.component};
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
    border: none;
    box-shadow: none;
    flex-shrink: 0;

    &:hover {
      background: ${({ theme }) => theme.palette.background.colorPrimaryBg};
      color: ${({ theme }) => theme.palette.text.heading};
    }
  }

  .ant-segmented-item-selected {
    background: ${({ theme }) => theme.palette.background.colorPrimaryBg};
    color: ${({ theme }) => theme.palette.text.heading};
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    .ant-segmented-item {
      font-size: 12px;
      gap: 4px;
      padding: 0 6px !important;
    }

    .ant-segmented-group {
      gap: 6px;
    }
    .ant-segmented-item-label {
      padding: 0 !important;
    }
  }
`;

export const StyledTabsContent = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 6px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    gap: 4px;
  }
`;

export const StyledSegmentWrapper = styled.div`
  width: 100%;
  border-bottom: 1px solid ${({ theme }) => theme.border.color};
`;

export const StyledSegmentedContent = styled.div`
  max-width: calc(${({ theme }) => theme.sizes.mainContentWidth});
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin: 0 auto;
`;
