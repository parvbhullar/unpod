import styled from 'styled-components';
import { Typography } from 'antd';

export const StyledContainer = styled.div`
  /*display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;*/
  padding: 30px;
  width: 100%;
  max-width: 530px;
  margin: 0 auto;
  text-align: center;

  &.has-org {
    margin: 0;
  }
`;

export const StyledTitle = styled(Typography.Title)`
  margin-bottom: 12px !important;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 30px !important;
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

export const StylesButtonWrapper = styled.div`
  text-align: center;
  margin-bottom: 20px;
`;

export const StylesImageWrapper = styled.div`
  position: relative;
  width: 110px;
  height: 110px;
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: 4px;
  overflow: hidden;
  margin: 0 auto 20px;
`;
