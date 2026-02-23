import styled from 'styled-components';
import {Button, Form, Input, Upload} from 'antd';

const {Dragger} = Upload;

export const StyledFormItem = styled(Form.Item)`
  border-bottom: 1px solid #dbdbdb;
  margin-bottom: 0;
`;

export const StyledInput = styled(Input)`
  padding: 0;
  border-radius: 0;
  font-size: 16px;
`;
export const StyledIcon = styled.div`
  padding: 0;
  border-radius: 0;
  font-size: 16px;
`;

export const StyledUploadContent = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
`;

export const StyledDragger = styled(Dragger)`
  display: inline-flex;
  flex-direction: column;
  width: 100%;
  border-radius: 8px;
  margin-bottom: 8px;

  .ant-upload-drag {
    border-width: 2px;
  }

  .ant-upload-btn {
    padding: 16px !important;
  }
`;

export const StyledCoverWrapper = styled.div`
  position: relative;
  width: 100%;
  height: 130px;
  border-radius: 8px;
  overflow: hidden;
`;

export const StyledDelContainer = styled.div`
  position: absolute;
  height: 22px;
  width: 22px;
  right: 10px;
  top: 10px;
  background-color: #ccc8c8;
  opacity: 0.75;
  border-radius: 50%;
  padding: 3px;
  cursor: pointer;

  .remove-cover-handle {
    color: ${({theme}) => theme.palette.text.secondary};
    vertical-align: unset;
  }

  &:hover,
  ${StyledCoverWrapper}:hover ~ & {
    background-color: #868383 !important;
    opacity: 1 !important;

    .remove-cover-handle {
      color: ${({theme}) => theme.palette.background.default};
      opacity: 1;
    }
  }
`;

export const StyledButton = styled(Button)`
  padding: 4px 15px !important;
  height: 36px !important;
`;
