import styled from 'styled-components';
import { Button } from 'antd';

export const StyledRoot = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  background: ${({ theme }) => theme.palette.common.white};
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 16px;
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  transition:
    box-shadow 0.2s,
    border-color 0.2s,
    transform 0.18s;

  &:hover {
    box-shadow: ${({ theme }) => theme.component.card.boxShadow};
    transform: scale(1.03);
    z-index: 2;
  }

  &.selected {
    border-color: ${({ theme }) => theme.palette.primary};
    box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: row;
    align-items: center;
  }
`;

export const StyledMainContent = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 12px;
  position: relative;
`;

export const StyledIconWrapper = styled.div`
  background: ${({ theme }) => theme.palette.background.component};
  border-radius: 16px;
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
`;

export const StyledMainInfo = styled.div`
  align-self: center;

  & .ant-typography {
    margin-bottom: 0 !important;
    font-size: 12px;
  }
`;

export const StyledActionWrapper = styled.div<{ $extra?: boolean }>`
  display: flex;
  align-items: flex-end;
  justify-content: ${({ $extra }) => ($extra ? 'space-between' : 'center')};
  gap: 12px;
`;

export const StyledButton = styled(Button)`
  padding: 0 9px !important;
  height: 28px;
`;
