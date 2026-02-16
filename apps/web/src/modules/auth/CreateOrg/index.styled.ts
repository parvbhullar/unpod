import styled from 'styled-components';
import { Typography } from 'antd';

export const StyledContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 30px;
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto 16px;
  background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 16px;
  }
`;

export const StyledTitle = styled(Typography.Title)`
  margin-bottom: 12px !important;
  font-size: 26px !important;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 21px !important;
  }
`;

export const StyledSubTitle = styled(Typography.Title)`
  font-weight: normal !important;
  margin-top: 0 !important;
  margin-bottom: 32px !important;
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    margin-bottom: 26px !important;
  }
`;

export const StylesImageWrapper = styled.div`
  position: relative;
  width: 80px;
  height: 80px;
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 20px;
`;
