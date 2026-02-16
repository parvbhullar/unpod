import styled from 'styled-components';
import { Button, Input } from 'antd';
import { GlobalTheme } from '@unpod/constants';

const { TextArea } = Input;

export const StyledContainer = styled.div`
  background-color: ${({ theme }: { theme: GlobalTheme }) =>
    theme.palette.background.paper};
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
  position: relative;
  padding: 12px;
  border-radius: 24px;
  overflow: visible;
  transition: all 0.2s ease;

  @media (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.md}px) {
    max-width: 100%;
    border-radius: 20px;
    padding: 10px;
  }

  @media (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.sm}px) {
    border-radius: 16px;
    padding: 8px;
  }
`;

export const StyledInput = styled(TextArea)`
  padding: 4px 8px;
  resize: none;
  font-size: 15px;
  line-height: 1.5;

  &::placeholder {
    color: ${({ theme }: { theme: GlobalTheme }) =>
      theme.palette.text.secondary};
    opacity: 0.6;
  }
`;

export const StyledMainContent = styled.div`
  margin-bottom: 8px;
  transition: all 0.3s ease;
  min-height: 40px;
  height: auto;

  &.active {
    min-height: 100px;
    height: auto;
  }

  .ant-form-item {
    margin-bottom: 0;
  }
`;

export const StyledBottomBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 6px;

  @media (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.sm}px) {
    flex-wrap: wrap;
  }
`;

export const StyledIconButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px !important;
  height: 32px !important;
  min-width: 32px;
  color: ${({ theme }: { theme: GlobalTheme }) => theme.palette.text.secondary};
  transition: all 0.2s ease;

  &:hover {
    background: ${({ theme }: { theme: GlobalTheme }) =>
      theme.palette.background.default} !important;
    color: ${({ theme }: { theme: GlobalTheme }) =>
      theme.palette.primary} !important;
  }
`;

export const StyledButton = styled(Button)`
  height: 32px !important;
  transition: all 0.2s ease;

  &:hover:not(:disabled) {
    transform: scale(1.05);
    box-shadow: 0 2px 8px
      ${({ theme }: { theme: GlobalTheme }) => theme.palette.primary}40;
  }

  &:active:not(:disabled) {
    transform: scale(0.95);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
`;

export const VoiceOverlay = styled.div<{ show?: boolean }>`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  min-height: 120px;
  background: rgba(255, 255, 255, 1);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  border-radius: 20px;
  opacity: ${(props) => (props.show ? 1 : 0)};
  z-index: ${(props) => (props.show ? 2000000 : 0)};
  transform: ${(props) => (props.show ? 'scale(1)' : 'scale(0.5)')};
  transition:
    opacity 0.4s ease-in-out,
    transform 0.3s ease-in-out;
`;

export const CloseButton = styled.button`
  position: absolute;
  top: 10px;
  right: 15px;
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #555;

  &:hover {
    color: black;
  }
`;
