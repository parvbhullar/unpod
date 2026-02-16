import styled from 'styled-components';
import {
  Button,
  Form,
  Input,
  Row,
  Select,
  Space,
  Typography,
  Upload,
} from 'antd';
import { GlobalTheme } from '@unpod/constants';

const { Dragger } = Upload;
const { Text } = Typography;

export const StyledInvitationRow = styled(Space)`
  display: flex;

  .ant-space-item {
    flex: 1;
    min-width: 160px;

    &:nth-child(3) {
      flex: 0;
      min-width: auto;
    }
  }
`;

export const StyledContainer = styled.div`
  max-height: 100%;
`;

export const StyledFormItem = styled(Form.Item)`
  border-bottom: 1px solid #dbdbdb;
  margin-bottom: 0;
`;
export const StyledInput = styled(Input)`
  padding: 8px 0;
  font-size: 16px;
`;

export const StyledSelect = styled(Select)`
  padding: 8px 0;
  font-size: 16px;

  .ant-select-selector {
    padding: 0 !important;
  }

  .ant-select-selection-placeholder {
    color: rgba(0, 0, 0, 0.35);
    font-size: 16px;
  }
`;

export const StyledTextArea = styled(Input.TextArea)`
  padding: 8px 0;
  resize: none;
`;
export const StyledButton = styled(Button)`
  padding: 4px 15px !important;
  height: 36px !important;
`;

export const StyledStickyButton = styled(StyledButton)`
  background-color: ${({ theme }: { theme: GlobalTheme }) =>
    theme.palette.background.default} !important;
  position: sticky;
  bottom: 5px;
  z-index: 100;
`;

export const StyledRowHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;

  .ant-row {
    flex: 1;
  }

  &::before {
    content: '';
    display: block;
    width: 18px;
    height: 18px;
    margin-bottom: 16px;
  }

  @media screen and (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.sm}px) {
    display: none;
  }
`;

export const StyledRow = styled(Row)`
  display: flex;
  margin-bottom: 16px;
`;

export const StyledList = styled.div`
  display: flex;
  flex-direction: column;
  row-gap: 12px;
  margin-bottom: 20px;

  @media screen and (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.sm}px) {
    row-gap: 24px;
  }
`;

export const StyledActionLabel = styled(Text)`
  display: block;
  text-align: right;

  @media screen and (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.sm}px) {
    text-align: left;
  }
`;

export const StyledMediaWrapper = styled.div`
  position: relative;
  margin: 0 0 20px 0;
`;

export const StyledDragger = styled(Dragger)`
  display: inline-flex;
  flex-direction: column;
  width: 100%;
  border-radius: 8px;

  .ant-upload-drag {
    border-width: 2px;
  }

  .ant-upload-btn {
    padding: 16px !important;
  }
`;
