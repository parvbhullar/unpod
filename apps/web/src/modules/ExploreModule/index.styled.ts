import styled from 'styled-components';
import { Typography } from 'antd';

export const StyledContainer = styled.div`
  margin: 16px auto 40px auto;
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
`;

export const StyledHiddenTitle = styled(Typography.Title)`
  display: none;
`;

export const StyledTitle = styled(Typography.Title)`
  font-size: 48px !important;
  font-weight: 700 !important;
  margin-bottom: 12px !important;
  text-align: center;
  color: ${({ theme }) => theme.palette.primary} !important;
  font-family: 'Berkshire Swash', cursive;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    font-size: 42px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    font-size: 38px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 34px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 28px !important;
  }
`;
