import styled from 'styled-components';
import type { ComponentType } from 'react';
import { Button, Input } from 'antd';
import { lighten } from 'polished';
import AppCustomMenus from '@unpod/components/common/AppCustomMenus';

export const StyledIconButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 !important;
  height: 36px !important;

  &:hover {
    background: transparent !important;
  }
`;

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

export const StyledKbActions = styled.div`
  color: ${({ theme }) => theme.palette.text.primary};
  border-top: 1px solid ${({ theme }) => lighten(0.05, theme.border.color)};
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 10px;
  cursor: pointer;

  &.all-selected,
  &:hover {
    color: ${({ theme }) => theme.palette.primary};
  }
`;
