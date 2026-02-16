import styled from 'styled-components';
import { Button } from 'antd';

export const StyledTitleContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background-color: ${({ theme }) => theme.palette.background.component};
  border-radius: ${({ theme }) => theme.radius.base}px;
  padding: 8px;
  margin-bottom: 12px;
  .bold {
    font-weight: bold;
  }
`;

export const StyledTabsWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
`;

export const StyledButton = styled(Button)`
  padding: 0 10px !important;
  height: 28px;
`;

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
`;
