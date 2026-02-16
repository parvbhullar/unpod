import styled from 'styled-components';
import { Button, Collapse } from 'antd';
import { rgba } from 'polished';
import { GlobalTheme } from '@unpod/constants';

export const StyledCollapse = styled(Collapse)`
  background-color: transparent;
  display: flex;
  flex-direction: column;
  gap: 20px;

  & .ant-collapse-item,
  & .ant-collapse-item:last-child {
    border: 1px solid
      ${({ theme }: { theme: GlobalTheme }) => theme.palette.background.default};
    border-radius: ${({ theme }: { theme: GlobalTheme }) =>
      theme.component.card.borderRadius};
    box-shadow: ${({ theme }: { theme: GlobalTheme }) =>
      theme.component.card.boxShadow};

    & .ant-collapse-header {
      background-color: ${({ theme }: { theme: GlobalTheme }) =>
        theme.palette.background.default};
      border-radius: ${({ theme }: { theme: GlobalTheme }) =>
        theme.component.card.borderRadius};
      align-items: center;
    }

    &.ant-collapse-item-active {
      & .ant-collapse-header {
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
      }
    }

    & .ant-collapse-content-box {
      padding-block: 16px 6px !important;
      background-color: ${({ theme }: { theme: GlobalTheme }) =>
        rgba(theme.palette.primary, 0.16)};
      border-bottom-left-radius: ${({ theme }: { theme: GlobalTheme }) =>
        theme.component.card.borderRadius};
      border-bottom-right-radius: ${({ theme }: { theme: GlobalTheme }) =>
        theme.component.card.borderRadius};
    }
  }
`;

export const StyledIconButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 22px !important;
  min-width: 22px !important;
  width: 22px !important;
  padding: 3px !important;
`;

export const StyledSuccessButton = styled(StyledIconButton)`
  background-color: ${({ theme }: { theme: GlobalTheme }) =>
    theme.palette.success};
`;

export const StyledErrorButton = styled(StyledIconButton)`
  background-color: ${({ theme }: { theme: GlobalTheme }) =>
    theme.palette.error};
`;

export const StyledWarningButton = styled(StyledIconButton)`
  background-color: ${({ theme }: { theme: GlobalTheme }) =>
    theme.palette.warning};
`;
