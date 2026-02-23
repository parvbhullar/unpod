import styled from 'styled-components';
import {Divider, Input, Select, Space, Typography} from 'antd';
import {GlobalTheme} from '@unpod/constants';

export const StyledDivider = styled(Divider)`
  margin: 12px 0;
`;

export const StyledBottomBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  position: absolute;
  top: auto;
  bottom: 0;
  width: 100%;
`;

export const StyledMainContent = styled.div`
  margin-top: 6px;
  margin-bottom: 12px;
  transition: all 0.4s linear;
  min-height: 86px;
  height: auto;
`;

export const StyledInput = styled(Input.TextArea)`
  padding: 4px 0;
  resize: none;
  background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.background.component};
`;

export const StyledSpace = styled(Space)`
  opacity: 0;
  transition: opacity 0.3s ease-in;

  &.active {
    opacity: 1;
  }
`;

export const StyledParentContainer = styled.div`
  padding: 0;
`;

export const StyledParent = styled(Typography.Paragraph)`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 0 !important;

  .ant-typography {
    margin-bottom: 0;
    flex: 1;
  }
`;

export const StyledTopBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: nowrap;
  gap: 16px;
  margin-bottom: 16px;

  & .ant-select-selection-item {
    border-radius: 5px !important;
    height: 18px !important;
  }
`;

export const StyledIconWrapper = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px;
  background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.primary}33;
  border: 1px solid
    ${({theme}: { theme: GlobalTheme }) => theme.palette.primary}33;
  border-radius: 5px;
  color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.primary}99 !important;
`;

export const StylesPilotLogo = styled.div`
  position: relative;
  width: 30px;
  height: 30px;
  // border: 1px solid ${({theme}: { theme: GlobalTheme }) =>
  theme.border.color};
  border: 1px solid
    ${({theme}: { theme: GlobalTheme }) => theme.palette.primary}33;
  border-radius: 5px;
  overflow: hidden;
`;

export const StyledSelect = styled(Select)`
  .ant-select-selection-item {
    font-weight: 600;
  }
`;

export const StyledCloseButton = styled.div`
  padding: 3px 4px;
  cursor: pointer;
  border-radius: 5px;
  margin-left: -5px;

  &:hover {
    background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.background.colorPrimaryBg};
  }
`;

export const StyledPilotRoot = styled.div`
  background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.background.default};
  width: ${({theme}: { theme: GlobalTheme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  border-radius: ${({theme}: { theme: GlobalTheme }) =>
  theme.component.card.borderRadius};
  box-shadow: 0 4px 4px 4px rgba(0, 0, 0, 0.01);
  padding: 16px;
  margin: auto auto 20px;
  position: sticky;
  bottom: 20px;
  top: auto;
  z-index: 101;
`;

export const StyledPilotContainer = styled.div`
  position: relative;
  background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.background.default};
  border-radius: ${({theme}: { theme: GlobalTheme }) =>
  `${theme.radius.base}px`};
  padding: 0 100px 16px 0;
  transition: all 0.25s linear;
  // max-height: 65px;
  min-height: 1px;
  flex: 1;
  width: 100%;
  max-width: 100%;
  // overflow: hidden;

  &.focused {
    // height: auto;
    // max-height: 100%;
    padding: 0 0 50px 0;
    // overflow: visible;
  }
`;

export const StyledOverlay = styled.div`
  position: absolute;
  height: 100%;
  width: 100%;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: rgba(245, 245, 245, 0.15);
  opacity: 0;
  visibility: hidden;
  z-index: 100;
  transition: all 0.25s linear;

  &.focused {
    opacity: 1;
    visibility: visible;
  }
`;
