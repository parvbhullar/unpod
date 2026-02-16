import styled from 'styled-components';
import { Typography } from 'antd';

const { Title } = Typography;

export const StyledTitle = styled(Title)`
  font-size: 42px !important;
  font-weight: 500 !important;
  margin-bottom: 12px !important;
  text-align: center;
  color: ${({ theme }) => theme.palette.primary} !important;

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

export const StyledActionsContainer = styled.div`
  margin: 0 auto;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-block: 0 70px;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    margin-block: 0 20px;
  }
`;
