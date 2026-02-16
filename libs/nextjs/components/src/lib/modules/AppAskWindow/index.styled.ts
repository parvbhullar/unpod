import styled from 'styled-components';
import { Input, Select, Typography } from 'antd';

export const StyledTopBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: nowrap;
  gap: 16px;
  margin-bottom: 16px;
`;

export const StyledIconWrapper = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px;
  background-color: ${({ theme }) => theme.palette.primary}33;
  border: 1px solid ${({ theme }) => theme.palette.primary}33;
  border-radius: 5px;
  color: ${({ theme }) => theme.palette.primary}99 !important;
`;

export const StylesPilotLogo = styled.div`
  position: relative;
  width: 30px;
  height: 30px;
  // border: 1px solid ${({ theme }) => theme.border.color};
  border: 1px solid ${({ theme }) => theme.palette.primary}33;
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
    background-color: ${({ theme }) => theme.palette.background.colorPrimaryBg};
  }
`;

export const StyledDescriptionWrapper = styled.div`
  opacity: 1;
  transition: all 0.2s ease-in;
  height: auto;
`;

export const StyledBottomBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
`;

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 20px auto;
  position: relative;
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  padding: 16px;
  z-index: 101;

  &.sticky {
    margin: auto auto 20px;
    position: sticky;
    bottom: 20px;
    top: auto;
    z-index: 101;
  }
`;

export const StyledContainer = styled.div`
  /*min-height: 1px;
  height: 86px;*/
  margin-bottom: 12px;
  transition: all 0.4s linear;
  min-height: 86px;
  height: auto;

  &.active {
    min-height: 160px;
    height: auto;

    ${StyledDescriptionWrapper} {
      opacity: 1;
      height: auto;
    }
  }
`;

export const StyledInput = styled(Input.TextArea)`
  padding: 4px 0;
  resize: none;
`;

export const StyledOverlay = styled.div`
  position: fixed;
  height: 100vh;
  width: 100vw;
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

export const StyledEscapeText = styled(Typography.Paragraph)`
  text-align: center;
  /*background-color: ${({ theme }) => theme.palette.background.default};
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;*/
  margin: 0 auto -13px !important;
  // padding: 10px 18px;
  /*border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};*/
`;
