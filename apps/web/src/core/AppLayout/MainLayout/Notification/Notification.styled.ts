'use client';
import styled from 'styled-components';
import { List } from 'antd';
import { rgba } from 'polished';

export const ListDate = styled.span`
  font-size: ${({ theme }) => theme.font.size.sm};
  color: #bfbfbf;
`;
export const StyledListItemWrapper = styled(List.Item)<{ $isRead?: boolean }>`
  cursor: pointer;
  box-shadow: ${({ $isRead }) =>
    $isRead
      ? '0 2px 3px rgba(31, 31, 31, 0.1)'
      : '0 2px 5px rgba(31, 31, 31, 0.1)'};
  background-color: ${({ $isRead, theme }) =>
    $isRead
      ? theme.palette.background.paper
      : rgba(theme.palette.primary, 0.1)};
  border-radius: 8px;
  padding: 15px 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  //border : 1px solid ${({ theme }) =>
    theme.border.color}; need to add this border

  &:not(:last-child) {
    margin-bottom: 15px;
  }

  & .ant-list-item-meta {
    width: 100%;
  }

  & .ant-list-item-meta-title {
    font-size: ${({ theme }) => theme.font.size.lg};
    color: ${({ theme }) => theme.palette.text.heading};
  }

  & .ant-list-item-action {
    margin-left: auto;
  }
`;

export const NotificationIconWrapper = styled.a`
  position: relative;

  &:after {
    content: '';
    position: absolute;
    right: 2px;
    top: -3px;
    z-index: 3;
    width: 8px;
    height: 8px;
    background-color: orange;
    border: 1px solid white;
    border-radius: 50%;

    @media (min-width: ${({ theme }) => theme.breakpoints.xxl + 320}px) {
      width: 8px;
      height: 8px;
    }
  }

  & img {
    @media (min-width: ${({ theme }) => theme.breakpoints.xxl + 320}px) {
      width: 24px;
    }
  }
`;
