import styled from 'styled-components';
import { Button } from 'antd';

export const StyledButton = styled(Button)`
  display: flex;
  align-items: center;
  padding: 4px 10px !important;
  height: 32px !important;
  gap: 6px;
`;

export const StyledEditRoot = styled.div`
  margin: 24px 0 0 0;
`;

export const IconWrapper = styled.span`
  cursor: pointer;
`;
