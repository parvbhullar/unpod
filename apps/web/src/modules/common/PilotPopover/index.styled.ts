import styled from 'styled-components';
import type { ComponentType } from 'react';
import { Button, Input } from 'antd';
import { lighten } from 'polished';
import AppCustomMenus from '@unpod/components/common/AppCustomMenus';

export const StyledKbMenus = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 0 0 0;
  border-radius: 14px;
  overflow: hidden;
`;

export const StyledMenus = styled(AppCustomMenus as ComponentType<any>)`
  min-width: 200px;
  width: 100%;
  max-width: 260px;

  & .app-custom-menu-item {
    border-radius: 10px;
  }
`;

export const StyledInputWrapper = styled.div`
  padding: 0 10px 10px 10px;
  border-bottom: 1px solid ${({ theme }) => lighten(0.05, theme.border.color)};
`;

export const StyledSearchInput = styled(Input)`
  border-radius: 10px;
`;

export const StylesPilotLogo = styled.div`
  position: relative;
  width: 24px;
  height: 24px;
  border: 1px solid ${({ theme }) => theme.palette.primaryActive};
  border-radius: 5px;
  overflow: hidden;
`;

export const StyledIconWrapper = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px;
  background-color: ${({ theme }) => theme.palette.primaryHover};
  border: 1px solid ${({ theme }) => theme.palette.primaryActive};
  border-radius: 5px;
  color: ${({ theme }) => theme.palette.primary}99 !important;
`;

export const StyledButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px !important;
  height: 36px !important;
`;
