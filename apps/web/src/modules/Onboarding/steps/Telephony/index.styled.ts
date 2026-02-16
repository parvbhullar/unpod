import styled from 'styled-components';
import { Card } from 'antd';

export const StyledContainer = styled.div`
  display: flex;
  justify-content: center;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 40px;
  margin-top: 40px;
`;

export const StyledNumber = styled.span`
  font-size: 32px !important;
  font-weight: bold;
  max-width: 425px !important;
  color: ${({ theme }) => theme.palette.primary} !important;
  margin: 0 !important;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 24px !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    font-size: 18px !important;
  }
`;

export const StyledCard = styled(Card)`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
`;
