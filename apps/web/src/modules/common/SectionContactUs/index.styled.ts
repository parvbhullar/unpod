import styled from 'styled-components';
import { Typography } from 'antd';

const { Title } = Typography;

export const StyledContainer = styled.div`
  max-width: 90%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 24px;
  border-radius: 30px;

  @media (max-width: 992px) {
    max-width: 100%;
  }
`;

export const StyledContent = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  row-gap: 16px;
  max-width: 700px;
  text-align: center;

  > *:nth-child(2) {
    margin-bottom: 12px !important;
  }
`;

export const StyledTitle = styled(Title)`
  font-family: 'Oxanium', sans-serif;
  font-size: 40px !important;
  font-weight: 600 !important;
  margin-bottom: 0 !important;

  color: ${({ theme }) => theme.palette.text.heading} !important;

  & .text-active {
    color: ${({ theme }) => theme.palette.primary} !important;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    font-size: 34px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 28px !important;
  }
`;

export const StyledSubTitle = styled(Title)`
  font-size: 18px !important;
  font-weight: 400 !important;
  margin: 0 auto !important;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 16px !important;
  }
`;
