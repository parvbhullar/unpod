import styled from 'styled-components';
import {Button, Form, Upload} from 'antd';

const {Dragger} = Upload;

export const StyledForm = styled(Form)`
  margin: auto;
  padding-top: 12px;
  width: 430px;
  max-width: 100%;
`;
export const StyledDragger = styled(Dragger)`
  display: inline-flex;
  flex-direction: column;
  width: 100%;
  border-radius: 8px;
  margin-bottom: 16px;

  .ant-upload-drag {
    border-width: 2px;
  }

  .ant-upload-btn {
    padding: 16px !important;
  }
`;

export const StyledActions = styled.div`
  display: flex;
  flex-direction: column;
  text-align: center;
  justify-content: center;
  gap: 12px;
`;

export const StyledButton = styled(Button)`
  margin-top: 14px;
  padding: 4px 15px !important;
  height: 36px !important;
`;
