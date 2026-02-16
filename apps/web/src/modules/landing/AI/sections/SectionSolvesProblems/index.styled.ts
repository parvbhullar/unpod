import styled from 'styled-components';
import { Typography } from 'antd';

const { Title } = Typography;

export const StyledTitle = styled(Title)`
  font-family: 'Oxanium', sans-serif;
  font-size: 36px !important;
  font-weight: 600 !important;
  margin-bottom: 24px !important;
  max-width: 430px;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    max-width: 100%;
  }

  & .text-active {
    color: ${({ theme }) => theme.palette.primary} !important;
  }
`;

export const StyledSubTitle = styled(Title)`
  font-family: 'Oxanium', sans-serif;
  font-size: 20px !important;
  font-weight: 500 !important;
  margin: 0 !important;
`;

export const StyledImageWrapper = styled.div`
  min-width: 50%;
  text-align: right;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    order: 1;
    text-align: center;
  }
`;

export const StyledTextContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-self: flex-end;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    text-align: center;
    order: 2;
  }
`;

export const StyledContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 60px;
  max-width: 1200px;
  margin: 0 auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    flex-direction: column;
  }

  &.reverse-position {
    ${StyledImageWrapper} {
      text-align: left;
      order: 1;
    }

    ${StyledTextContainer} {
      order: 2;
    }
  }
`;
