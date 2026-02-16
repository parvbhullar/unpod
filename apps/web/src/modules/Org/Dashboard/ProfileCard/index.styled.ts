import styled from 'styled-components';
import { Button } from 'antd';

export const StyledRoot = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 12px;
  background: ${({ theme }) => theme.palette.common.white};
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: border-color 0.3s ease;
  height: 100%;

  &.selected,
  &:hover {
    border-color: ${({ theme }) => theme.palette.primary};
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    align-items: center;
  }
`;

export const StyledMainContent = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

export const StyledIconWrapper = styled.div`
  background: ${({ theme }) => theme.palette.background.component};
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
`;

export const StyledMainInfo = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;

  & .ant-typography {
    margin-bottom: 0 !important;
  }
`;

export const StyledActionWrapper = styled.div<{ $extra?: boolean }>`
  display: flex;
  align-items: center;
  flex-shrink: 0;
  justify-content: ${({ $extra }) => ($extra ? 'space-between' : 'center')};
  gap: 12px;
`;

export const StyledButton = styled(Button)`
  //padding: 0 9px !important;
  //height: 28px;
`;
