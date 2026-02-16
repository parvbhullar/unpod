import styled from 'styled-components';
import { Button, Divider, Input, Typography } from 'antd';

const { TextArea } = Input;

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

export const StyledPilotRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.component};
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 95%;
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  // border: 3px solid ${({ theme }) => theme.palette.background.component};
  border: 1px solid ${({ theme }) => theme.border.color};
  // box-shadow: 0 4px 4px 4px rgba(0, 0, 0, 0.01);
  padding: 16px;
  margin: auto auto 20px;
  position: sticky;
  bottom: 25px;
  top: auto;
  z-index: 101;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    margin-bottom: 5px;
    bottom: 10px;
  }
`;

export const StyledPilotContainer = styled.div`
  position: relative;
  background-color: ${({ theme }) => theme.palette.background.component};
  border-radius: ${({ theme }) => `${theme.radius.base}px`};
  padding: 0 100px 16px 0;
  transition: all 0.25s linear;
  // max-height: 65px;
  min-height: 1px;
  flex: 1;
  width: 100%;
  max-width: 100%;
  overflow: hidden;

  &.focused {
    height: auto;
    // max-height: 100%;
    padding: 0 0 50px 0;
    overflow: visible;
  }
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

export const StyledButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  gap: 8px;
`;

export const StyledInput = styled(TextArea)`
  padding: 4px 0;
  resize: none;
  background-color: ${({ theme }) => theme.palette.background.component};
`;

export const StyledDivider = styled(Divider)`
  margin: 12px 0;
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
