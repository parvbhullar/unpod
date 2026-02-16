import styled from 'styled-components';
import { Button, Tag } from 'antd';

export const StyledRoot = styled.div`
  padding: 12px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  cursor: pointer;
  transition: border-color 0.3s ease;

  @media (max-width: 768px) and (min-width: 326px) {
    flex-direction: row !important;
    height: auto !important;

    .ant-typography {
      font-size: 13px;
    }
  }
  &.selected,
  &:hover {
    border-color: ${({ theme }) => theme.palette.primary};
  }
`;

export const StyledContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

export const StyledIconWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${({ theme }) => theme.palette.background.component};
  border-radius: 50%;
  padding: 5px;
  color: ${({ theme }) => theme.palette.primary};
`;

export const StyledInfoContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;

  & .ant-typography {
    margin-bottom: 0 !important;
  }
`;

export const StyledActions = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

export const StyledTag = styled(Tag)`
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  padding: 2px 8px;
`;

export const StyledButton = styled(Button)`
  padding: 0 9px !important;
  height: 28px;

  &.ant-btn-circle {
    width: 28px;
    min-width: 28px !important;
  }
`;
