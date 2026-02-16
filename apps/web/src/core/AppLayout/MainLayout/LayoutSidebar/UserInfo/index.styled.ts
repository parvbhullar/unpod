import styled from 'styled-components';
import type { ComponentType } from 'react';
import { Menu } from 'antd';
import UserAvatar from '@unpod/components/common/UserAvatar';

export const StyledMenu = styled(Menu)`
  background-color: transparent;
  border: 0 none !important;
  font-size: 13px;
  font-weight: 600;

  & .ant-menu-item {
    margin-bottom: 16px;
    height: 48px;
    padding-inline: 22px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    background-color: ${({ theme }) => theme.palette.background.default};

    &.ant-menu-item-selected,
    &:hover {
      color: ${({ theme }) => theme.palette.primary} !important;
      background-color: ${({ theme }) =>
        theme.palette.background.default} !important;

      & .ant-menu-item-icon {
        color: ${({ theme }) => theme.palette.primary};
      }
    }

    .ant-menu-item-icon {
      font-size: 24px;
      vertical-align: -0.5em;
      color: ${({ theme }) => theme.palette.text.light};
    }
  }
`;

export const UserInfoWrapper = styled.a`
  display: flex;
  align-items: center;
  //margin-left: 20px !important;
  font-size: ${({ theme }) => theme.font.size.base};
  color: ${({ theme }) => theme.palette.text.primary};

  @media screen and (min-width: ${({ theme }) =>
      theme.breakpoints.xxl} + 320px) {
    font-size: ${({ theme }) => theme.font.size.lg};
  }

  &:hover,
  &:focus {
    color: ${({ theme }) => theme.palette.text.primary};
  }
`;
export const UserImage = styled.img`
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;

  @media (min-width: ${({ theme }) => theme.breakpoints.xxl + 320}px) {
    width: 40px;
    height: 40px;
  }
`;
export const UserContent = styled.span`
  margin-left: 7px;
  align-items: center;
  display: none;

  @media (min-width: ${({ theme }) => theme.breakpoints.md}px) {
    display: flex;
  }

  & .anticon {
    font-size: 10px;

    @media (min-width: ${({ theme }) => theme.breakpoints.xxl + 320}px) {
      font-size: ${({ theme }) => theme.font.size.base};
    }
  }
`;

export const UserName = styled.span`
  margin-right: 5px;
  text-transform: capitalize;
`;

export const StyledUserAvatar = styled(UserAvatar as ComponentType<any>)`
  // transition: all 0.1s linear;
  // overflow: visible;
  // border-radius: ${({ theme }) => theme.radius.circle};
  //
  // & img {
  //   border-radius: ${({ theme }) => theme.radius.circle};
  // }
  //

  &:before {
    content: '';
    position: absolute;
    left: -12px;
    top: 50%;
    transform: translateY(-50%);
    display: block;
    width: 6px;
    height: 20px;
    border-radius: 0 4px 4px 0;
    background-color: transparent;
    transition: all 0.1s linear;
  }

  // &:hover,
  // &:focus {
  //   border-radius: 16px;
  //
  //   &:before {
  //     background-color: ${({ theme }) => theme.palette.primary};
  //   }
  //
  //   & img {
  //     border-radius: 16px;
  //   }
  // }

  &.active {
    &:before {
      background-color: ${({ theme }) => theme.palette.primary};
      height: 28px;
    }
  }
`;
