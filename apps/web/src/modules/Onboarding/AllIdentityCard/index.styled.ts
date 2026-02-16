import styled from 'styled-components';
import { Card } from 'antd';

export const StyledCard = styled(Card)`
  border-radius: 8px;
  padding: 22px 12px;
  color: ${({ theme }) => theme.palette.text.primary};
  background: ${({ theme }) => theme.palette.background.default};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow} !important;
  border: 1px solid ${({ theme }) => theme.palette.text.light};
  transition: border-color 0.2s ease;

  .ant-card-meta-title {
    font-family: ${({ theme }) => theme.font.family} !important;
    font-size: ${({ theme }) => theme.font.size.lg} !important;
    font-weight: ${({ theme }) => theme.font.weight.semiBold} !important;
    margin-bottom: 10px;
  }

  .ant-card-meta-description {
    font-family: ${({ theme }) => theme.font.family} !important;
    font-size: ${({ theme }) => theme.font.size.base} !important;
  }

  &:hover {
    border: 1px solid ${({ theme }) => theme.palette.infoBorder};
  }

  &.selected {
    border-color: ${({ theme }) => theme.palette.primary};
  }

  cursor: pointer;
`;

export const StyledCardIcon = styled.div<{ $bgColor?: string }>`
  color: ${({ theme }) => theme.palette.common.white};
  background: ${({ $bgColor }) => $bgColor} !important;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 auto 16px;
`;
