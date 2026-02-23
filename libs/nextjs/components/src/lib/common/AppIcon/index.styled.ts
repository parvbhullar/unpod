import styled from 'styled-components';
import {Button, Space} from 'antd';

export const StyledSpace = styled(Space)`
  padding: 3px 8px;
  border-radius: 4px;
  height: 30px;
  align-items: center;
  display: flex;
  width: 100%;
  cursor: pointer;

  &.ant-space .ant-space-item {
    display: flex;
    align-items: center;
  }

  :hover {
    background-color: #00000008;
  }
`;

export const StyledIconButton = styled(Button)`
  padding: 0;
  border: 0 none;
  box-shadow: none;
  width: auto !important;
`;
export const StyledButton = styled(Button)`
  padding: 3px 8px;
  border: 0 none;
  height: 30px !important;
  width: 100%;
  justify-content: flex-start !important;

  :hover {
    background-color: #00000008;
  }
`;
