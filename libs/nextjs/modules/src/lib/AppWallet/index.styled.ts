import styled from 'styled-components';
import { Button } from 'antd';

export const StyledHeader = styled.div`
  background-color: #1ec6a0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: ${({ theme }) => theme.radius.base}px;

  & .ant-typography {
    color: ${({ theme }) => theme.palette.common.white};
  }
`;

export const StyledContent = styled.div`
  flex: 1;
  padding: 20px 0 0 0;

  @media screen and (min-width: 480px) {
    flex-direction: row;
    justify-content: space-between;
  }
`;

export const StyledButton = styled(Button)`
  display: flex;
  align-items: center;
  padding: 4px 10px !important;
  height: 32px !important;
  gap: 6px;
`;

export const StyledAmountView = styled.div`
  margin-top: -10px;
  margin-bottom: 16px;
`;
