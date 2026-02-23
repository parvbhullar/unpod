import styled from 'styled-components';
import {Button, Divider, Input, Typography} from 'antd';

const {TextArea} = Input;

export const StyledBottomBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;

  transform: translateY(0);
  opacity: 1;
  transition: all 0.35s cubic-bezier(0.25, 1, 0.5, 1);
  will-change: transform, opacity;

  .SetBottom & {
    //align-self: flex-end;
    margin-top: 8px;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    justify-content: space-between;
  }
`;

export const StyledPilotRoot = styled.div`
  background-color: ${({theme}) =>
  theme.palette.background.default} !important;
  width: 95%;
  max-width: ${({theme}) => theme.sizes.mainContentWidth};
  border-radius: ${({theme}) => theme.component.card.borderRadius};
  box-shadow: ${({theme}) => theme.component.card.boxShadow};
  margin: auto auto 0;
  position: sticky;
  //padding-bottom: 10px;
  bottom: 0;
  top: auto;
  z-index: 101;

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    margin-bottom: 5px;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    bottom: 0;
    //padding-bottom: 22px;
    margin-bottom: 0;
  }
`;

export const StyledPilotContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  width: 100%;
  background: ${({theme}) => theme.palette.background.default};
  border-radius: 1.5rem;
  border: 1px solid ${({theme}) => theme.border.color};
  padding: 6px 6px;
  position: relative;

  transition: all 0.35s cubic-bezier(0.25, 1, 0.5, 1);
  will-change: padding, flex-direction, align-items, height;

  &.SetBottom {
    flex-direction: column;
    align-items: stretch;
  }

  &:focus-within {
    border-color: ${({theme}) => theme.palette.primary};
    box-shadow: 0 0 0 3px ${({theme}) => theme.palette.primary}15;
  }
`;

export const StyledContentWrapper = styled.div`
  display: flex;
  //align-items: flex-end;
  justify-content: center;
  width: 100%;
  background: ${({theme}) => theme.palette.background.default};
  border-radius: 1.5rem;
  position: relative;

  transition: all 0.35s cubic-bezier(0.25, 1, 0.5, 1);
  will-change: padding, flex-direction, align-items, height;

  &.SetBottom {
    flex-direction: column;
    align-items: stretch;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    flex-direction: column;
    gap: 12px;
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

export const StyledInputWrapper = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  transition: all 0.25s ease;

  .SetBottom & {
    width: 100%;
    align-items: stretch;
  }
`;

export const StyledInput = styled(TextArea)`
  flex: 1;
  resize: none;
  background: transparent !important;
  padding: 6px 8px;

  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  will-change: height, padding, margin;

  &::-webkit-scrollbar {
    display: none;
  }
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
