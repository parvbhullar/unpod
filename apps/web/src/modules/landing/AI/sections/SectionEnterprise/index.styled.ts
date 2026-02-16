import styled from 'styled-components';
import type { ComponentType } from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';

export const StyledPageSection = styled(AppPageSection as ComponentType<any>)`
  color: ${({ theme }) => theme.palette.common.white};

  & .ant-typography {
    color: ${({ theme }) => theme.palette.common.white};
  }
`;

export const StyledContainer = styled.div`
  text-align: center;
  margin: 0 auto;

  & .ant-btn {
    width: 100%;
    max-width: 300px;
  }
`;
