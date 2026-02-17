import styled from 'styled-components';
import { Button, Segmented, Typography } from 'antd';

const { Title } = Typography;

type ToggleButtonProps = {
  active?: boolean;
  disabled?: boolean;
}

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  flex: 1;
  height: calc(100vh - 10px);
  overflow-y: hidden;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    height: calc(100vh - 85px);
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    height: calc(100vh - 20px);
  }

  .ant-tabs-content {
    padding: 0 !important;
  }
`;

export const StyledTitleContainer = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
`;

export const StyledAgentHandle = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 10px;
`;

export const StyledAgentInput = styled.div`
  border: 0 none;
  padding: 4px 6px;
  cursor: pointer;
  height: 28px;
  gap: 8px;
  display: flex;
  align-items: center;
  border-radius: 6px;
  width: 240px;

  &:hover {
    background: ${({ theme }) => theme.palette.background.component};
  }

  .ant-typography {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 230px !important;
    display: block;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 180px;
    .ant-typography {
      max-width: 170px !important;
    }
  }
}
`;

export const StyledEditButton = styled(Button)`
  height: 36px;
  width: 40px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    height: 28px !important;
    width: 28px !important;
  }
`;
export const TitleWrapper = styled.div`
  width: 100%;
  max-width: 450px;

  @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    max-width: 180px;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xl + 168}px) {
    max-width: 280px;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 52}px) {
    max-width: 190px;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    max-width: 400px;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    max-width: 170px !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xss}px) {
    max-width: 130px !important;
  }
`;

export const StyledTitle = styled(Title)`
  margin-bottom: 0 !important;
  width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;

  @media (max-width: 768px) {
    font-size: 16px !important;
    line-height: 1.2;
  }
`;

export const StyledTitleWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    gap: 0;
  }

  & .ant-form-item {
    margin-bottom: 0 !important;
  }

  .ant-form-item-explain-error {
    position: absolute;
  }

  .title-input {
    height: 36px;
    font-size: 18px;
    font-weight: 600;

    @media (max-width: 768px) {
      height: 32px;
      font-size: 14px;
    }
  }

  @media (max-width: 768px) {
    svg {
      font-size: 14px;
    }
  }
`;

export const StyledIconWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 8px;
  svg {
    font-size: 21px;
  }

  @media (max-width: 768px) {
    svg {
      font-size: 15px;
    }
  }
`;

export const StyledActionIcon = styled.span`
  display: flex;
  justify-content: center;
  cursor: pointer;
  color: ${({ theme }) => theme.palette.success};
  padding: 5px;
  border-radius: ${({ theme }) => theme.radius.base}px;

  &.close-btn {
    color: ${({ theme }) => theme.palette.error};
  }

  &:hover {
    background-color: ${({ theme }) => theme.palette.background.component};
  }

  @media (max-width: 480px) {
    padding: 3px;
  }
`;

export const StyledSegmented = styled(Segmented)`
  padding: 0;

  .ant-segmented-item-label {
    min-height: 32px !important;
    line-height: 32px !important;
    font-size: 14px !important;
  }

  .ant-segmented-item-selected {
    background-color: ${({ theme }) => theme.palette.primary} !important;
    color: ${({ theme }) => theme.palette.common.white} !important;
  }
`;

export const StyledTab = styled.div`
  margin-bottom: 10px;
  .ant-tabs-nav::before {
    border-bottom: none !important;
  }
`;

export const StyledAgentRoot = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
`;

export const StyledDrawerWrapper = styled.div`
  .ant-drawer-body {
    overflow: hidden !important;
  }
`;

export const StyledContainer = styled.div`
  padding: 14px;
`;

export const StyledTabsWrapper = styled.div`
  display: flex;
  flex-direction: column;
  scrollbar-width: thin;

  .ant-tabs-nav-wrap {
    width: ${({ theme }) => theme.sizes.mainContentWidth};
    max-width: 100%;
    margin: 0 auto !important;
    flex: none !important;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      max-width: 100% !important;
    }

    @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
      flex: 1 !important;
    }
  }

  .ant-tabs-nav {
    position: sticky;
    top: 0;
    background: ${({ theme }) => theme.palette.background.default};
    z-index: 10;

    padding: 0 14px;

    @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
      padding: 0 0 0 14px;
    }
  }

  .ant-tabs-content-holder {
    flex: 1;
    width: 100% !important;
    padding-top: 14px;
  }

  .ant-tabs-top > .ant-tabs-nav {
    margin: 0 !important;
  }
`;

export const StickyFooter = styled.div`
  position: sticky;
  bottom: 0;
  background: ${({ theme }) => theme.palette.background.default};
  z-index: 99;
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto;
  padding: 14px;
  border-top: 1px solid ${({ theme }) => theme.border.color};
`;

export const StyledTabRoot = styled.div`
  scrollbar-width: thin;
  height: calc(100vh - 210px);
  overflow-y: auto;
  padding: 0 14px;
  overflow-x: hidden;
`;

export const StyledMainContainer = styled.div`
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto !important;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    width: 100%;
  }
`;

export const ToggleButton = styled.span<ToggleButtonProps>`
  background: ${({ active }) => (active ? '#6c47ff' : 'transparent')};
  color: ${({ active }) => (active ? '#fff' : '#888')};
  padding: 4px 16px;
  display: inline-flex;
  align-items: center;
  font-weight: 500;
  font-size: 16px;
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'pointer')};
  opacity: ${({ disabled }) => (disabled ? 0.5 : 1)};
  transition: background 0.2s;
  user-select: none;

  svg {
    margin-right: 8px;
  }
`;

export const StyledContent = styled.div`
  flex: 1;
  padding: 20px 0 0 0;

  @media screen and (min-width: 480px) {
    flex-direction: row;
    justify-content: space-between;
  }
`;
