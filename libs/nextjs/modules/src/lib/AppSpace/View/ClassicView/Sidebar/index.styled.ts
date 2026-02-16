import styled from 'styled-components';
import { Segmented } from 'antd';
import { rgba } from 'polished';

export const StyledSegmentedContainer = styled.div`
  padding: 6px 6px;
  border-block-end: 1px solid ${({ theme }) => theme.border.color};
  display: flex;
  align-items: center;
  background-color: ${({ theme }) => theme.palette.background.default};
`;

export const StyledSegmented = styled(Segmented)`
  &.ant-segmented {
    display: flex;
    width: 100%;
    background: ${({ theme }) => theme.palette.background.component} !important;
    border-radius: ${({ theme }) => theme.radius.base}px !important;
    padding: 4px !important;
    font-size: 13px;
    gap: ${({ theme }) => theme.space.sm};
  }

  .ant-segmented-group {
    display: flex;
    gap: ${({ theme }) => theme.space.xss};
    width: 100%;
  }

  .ant-segmented-item {
    padding: 4px 8px !important;
    border-radius: ${({ theme }) => theme.radius.sm}px !important;
    font-weight: 500;
    cursor: pointer;
    border: none !important;
    background: transparent !important;
    color: ${({ theme }) => theme.palette.text.secondary} !important;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: ${({ theme }) => theme.space.xss};
    white-space: nowrap;
    position: relative;
    z-index: 1;
    min-height: auto !important;
    flex: 1 1 0;
  }

  .ant-segmented-item-selected {
    background: ${({ theme }) => theme.palette.background.default} !important;
    color: ${({ theme }) => theme.palette.text.heading} !important;
    box-shadow: none !important;
  }

  .ant-segmented-item:hover:not(.ant-segmented-item-selected) {
    color: ${({ theme }) => theme.palette.text.secondary} !important;
    background: ${({ theme }) => rgba(theme.palette.primary, 0.08)} !important;
  }

  .ant-segmented-item-icon {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    font-size: 18px;
  }

  .ant-segmented-item-label {
    height: auto !important;
    line-height: normal !important;
    padding: 0 !important;
    min-height: auto !important;
  }

  .ant-segmented-thumb {
    display: none !important;
  }
`;

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  width: 320px;
  border-radius: ${({ theme }) => theme.component.card.borderRadius}
    ${({ theme }) => theme.component.card.borderRadius} 0 0;
  display: flex;
  overflow: hidden;
  flex-direction: column;
  position: relative;
`;

export const StyledStickyContainer = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  position: sticky;
  top: 0;
  z-index: 1;
`;

export const StyledItemsWrapper = styled.div`
  padding: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
`;
