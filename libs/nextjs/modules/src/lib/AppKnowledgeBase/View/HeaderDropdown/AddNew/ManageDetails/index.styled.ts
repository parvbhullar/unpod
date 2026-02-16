import styled from 'styled-components';
import { Button } from 'antd';

export const StyledButton = styled(Button)`
  display: inline-flex;
  align-items: center;
`;

export const StyledChoicesContainer = styled.div`
  padding-block-start: 20px;
`;

export const StyledRowContainer = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 12px;
`;

export const StyledDelButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: auto !important;
  height: auto !important;
  padding: 0;
  opacity: 0;
  transition: all 0.3s ease;
`;
