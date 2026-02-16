'use client';
import styled from 'styled-components';
import type { ComponentType } from 'react';
import { Tabs } from 'antd';
import AppPageSection from '@unpod/components/common/AppPageSection';

export const StyledContainer = styled.div`
  // width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto;
`;

export const StyledPageSection = styled(AppPageSection as ComponentType<any>)`
  color: ${({ theme }) => theme.palette.common.white};

  & .ant-typography {
    color: ${({ theme }) => theme.palette.common.white};
  }
`;

export const StyledTabs = styled(Tabs)`
  & .ant-tabs-tab .ant-tabs-tab-btn {
    color: ${({ theme }) => theme.palette.common.white};
  }
`;

export const StyledListContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  grid-gap: 24px;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  }
`;
