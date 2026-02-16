'use client';
import styled from 'styled-components';
import { Avatar, Menu, Space } from 'antd';
import SimpleBar from 'simplebar-react';

import { rgba } from 'polished';

export const StyledScrollbar = styled(SimpleBar)`
  display: flex;
  flex-direction: column;
  height: 100vh;

  & .simplebar-content-wrapper {
    outline: none;
  }

  & .simplebar-content {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    //padding: 12px;
    outline: none;
  }
`;

export const StyledHubMenus = styled(Menu)`
  border-inline-end: 0 none !important;
  max-height: 60vh;
  overflow-y: auto;

  & .ant-menu-item {
    padding: 8px 6px !important;

    & .ant-avatar {
      color: ${({ theme }) => theme.palette.common.white} !important;
    }
  }
`;

export const StyledMiniAvatar = styled(Avatar)<{
  $isAppLogo?: boolean;
  $avatarColor?: string;
  $isLogo?: boolean;
}>`
  width: ${({ $isAppLogo }) => ($isAppLogo ? '36px' : '44px')};
  height: ${({ $isAppLogo }) => ($isAppLogo ? '36px' : '44px')};
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 8px;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
  position: relative;
  overflow: inherit;
  background-color: transparent;
  color: ${({ theme }) => theme.palette.text.secondary} !important;
  border: none !important;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 40px;
    height: 40px;
  }

  &.org-avatar {
    font-size: 16px;
    transform: scale(1);
    translateX(-50%);
    font-weight: 600;
    color: #ffffff !important;
    background-color: ${({ theme, $avatarColor }) =>
      $avatarColor || theme.palette.primary} !important;

    &.placeholder-avatar {
      &:hover,
      &:focus {
        background-color: ${({ theme }) => theme.palette.primary} !important;
        color: #ffffff !important;
      }
    }
  }

  svg {
    display: block;
    font-size: 22px !important;
  }

  img {
    width: ${({ $isAppLogo }) => ($isAppLogo ? '36px' : '44px')};
    height: ${({ $isAppLogo }) => ($isAppLogo ? '36px' : '44px')};
    border-radius: 8px;
    transition: border-radius 0.2s ease;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      width: 36px;
      height: 36px;
    }
  }

  &:hover,
  &:focus {
    background-color: ${({ theme }) => rgba(theme.palette.primary, 0.1)};
    color: ${({ theme }) => theme.palette.text.heading} !important;
    & img {
      border-radius: 8px;
    }
  }

  &.partially-active,
  &.active {
    border-radius: 8px;
    background-color: ${({ theme, $isLogo, $avatarColor }) =>
      $isLogo
        ? 'transparent'
        : $avatarColor || theme.palette.primary} !important;
    color: ${({ $isLogo }) => ($isLogo ? 'transparent' : '#FFF')} !important;

    & img {
      border-radius: 8px;
    }
  }
`;

export const StyledMiniLogo = styled(Avatar)<{ $isAppLogo?: boolean }>`
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 12px;
  transition: background-color 0.2s ease;
  position: relative;
  overflow: inherit;
  background-color: transparent;

  img {
    width: ${({ $isAppLogo }) => ($isAppLogo ? '30px' : '36px')};
    height: ${({ $isAppLogo }) => ($isAppLogo ? '30px' : '36px')};
    border-radius: ${({ $isAppLogo }) => ($isAppLogo ? '6px' : '12px')};
  }

  &:hover,
  &:focus {
    background-color: ${({ theme }) => rgba(theme.palette.primary, 0.1)};
  }
`;

export const StyledMinibar = styled.div`
  display: flex;
  flex-direction: column;
  width: 72px;
  min-width: 72px;
  color: inherit;
  position: fixed;
  height: 100vh;
  z-index: 100;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 60px;
    min-width: 60px;
  }

  &:before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    z-index: 1;
    width: 100%;
    height: 100%;
    background-color: ${({ theme }) => theme.palette.background.default};
  }

  &.dark {
    &:before {
      background-color: ${() => rgba('black', 0.05)};
    }
  }

  [dir='rtl'] & {
    border-right: 0 none;
  }

  & a {
    color: inherit;
  }
`;

export const StyledInnerContainer = styled.div`
  position: relative;
  z-index: 3;
  display: flex;
  flex-direction: column;
`;

export const StyledMainMenus = styled(Space)`
  margin: 12px auto;

  & .ant-space-item {
    cursor: pointer;
  }
`;

export const StyledUserMenus = styled(Space)`
  text-align: center;
  position: sticky;
  bottom: 0;
  top: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: ${({ theme }) => theme.space.sm};
  margin: auto auto 0 auto;
  background-color: ${({ theme }) => theme.palette.background.default};
  padding: 10px 10px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 10px 10px;
  }

  & .ant-space-item {
    display: flex;
    justify-content: center;
    width: auto;
    cursor: pointer;
  }
`;
export const StyledOverlayLoader = styled.div`
  position: absolute !important;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.4);
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  display: flex;
  z-index: 1000;
`;

export const StyledDivider = styled.span`
  border-top: 1px solid ${({ theme }) => theme.border.color};
  width: 40px;
  display: flex;
`;
