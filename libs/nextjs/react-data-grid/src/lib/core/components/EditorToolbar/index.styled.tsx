import { Button, Input } from 'antd';
import styled from 'styled-components';
import { rgba } from 'polished';

export const StyledRoot = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
`;

export const StyledToolbarRoot = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 1px;
  padding: 5px;
  background-color: ${({ theme }: { theme: any }) =>
    rgba(theme.primaryColor, 0.11)};
  border: 1px solid ${({ theme }: { theme: any }) => theme.border.color};
  border-radius: ${({ theme }: { theme: any }) =>
    theme.radius?.base ?? theme.border?.radius ?? 6};
`;

export const StyledInput = styled(Input)`
  border-radius: ${({ theme }: { theme: any }) =>
    theme.radius?.base ?? theme.border?.radius ?? 6};

  &.ant-input-affix-wrapper {
    height: 36px;
  }

  & .ant-input-number-handler-wrap {
    border-start-end-radius: ${({ theme }: { theme: any }) =>
      theme.radius?.base ?? theme.border?.radius ?? 6};
    border-end-end-radius: ${({ theme }: { theme: any }) =>
      theme.radius?.base ?? theme.border?.radius ?? 6};
  }
`;

export const StyledButton = styled(Button)`
  &.selected {
    background-color: ${({ theme }: { theme: any }) =>
      rgba(theme.primaryColor, 0.17)};
  }
`;
export const StyledColorButton = styled(StyledButton)`
  background-color: transparent;
  display: flex;
  flex-direction: column;
`;

export const StyledFillColor = styled.div`
  width: 14px;
  height: 4px;
  margin-top: 2px;
`;
