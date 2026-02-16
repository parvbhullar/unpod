import React from 'react';
import { Breadcrumb, Tooltip } from 'antd';
import styled from 'styled-components';
import { truncateString } from '@unpod/helpers/StringHelper';
import { BreadcrumbItemType } from 'antd/es/breadcrumb/Breadcrumb';

export const StyledBreadcrumb = styled(Breadcrumb)`
  font-size: 11px;
  & ol {
    // flex-wrap: nowrap;

    li {
      text-transform: capitalize;
    }
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    display: none;
  }
`;

type AppBreadCrumbTitleProps = {
  title: string;
  length?: number;};

export const AppBreadCrumbTitle: React.FC<AppBreadCrumbTitleProps> = ({
  title,
  length = 60,
}) => {
  if (!title) return null;

  return title.length > length ? (
    <Tooltip title={title}>{truncateString(title, length, true)}</Tooltip>
  ) : (
    <span>{title}</span>
  );
};

type AppBreadCrumbProps = {
  items: BreadcrumbItemType[];};

const AppBreadCrumb: React.FC<AppBreadCrumbProps> = ({ items }) => {
  return <StyledBreadcrumb separator=">" items={items} />;
};

export default AppBreadCrumb;
