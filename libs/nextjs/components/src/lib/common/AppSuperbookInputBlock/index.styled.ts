import styled from 'styled-components';
import {
  Button,
  Checkbox,
  DatePicker,
  Input,
  InputNumber,
  Select,
  TimePicker,
  Typography,
  Upload,
} from 'antd';
import { rgba } from 'polished';

const { Paragraph } = Typography;
const { TextArea } = Input;

export const StyledTopBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 1em;

  & .ant-typography {
    margin-bottom: 0;
  }
`;

export const StylesLogoWrapper = styled.div`
  position: relative;
  width: 30px;
  height: 30px;
  border: 1px solid ${({ theme }) => theme.palette.primary}33;
  border-radius: 5px;
  overflow: hidden;
`;

export const StyledIconWrapper = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px;
  background-color: ${({ theme }) => theme.palette.primary}33;
  border: 1px solid ${({ theme }) => theme.palette.primary}33;
  border-radius: 5px;
  color: ${({ theme }) => theme.palette.primary}99 !important;
`;

export const StyledSelect = styled(Select)`
  .ant-select-selection-item {
    font-weight: 600;
  }
`;

export const StyledAppLabel = styled(Paragraph)`
  margin-bottom: 0 !important;
`;

export const StyledContainer = styled.div`
  margin-block: 10px;
`;

export const StyledInputNumber = styled(InputNumber)`
  width: 100%;
`;

export const StyledDatePicker = styled(DatePicker)`
  width: 100%;
`;

export const StyledTimePicker = styled(TimePicker)`
  width: 100%;
`;

export const StyledInput = styled(TextArea)`
  padding: 4px 0;
  resize: none;
`;

export const StyledBottomBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
`;

export const StyledBlockActions = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0;
  position: absolute;
  right: 20px;
  top: -15px;
  height: 36px;
  background-color: ${({ theme }) => theme.palette.background.default};
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  padding: 10px;
  z-index: 100;
  transition: all 0.3s ease;

  &:hover {
    color: ${({ theme }) => rgba(theme.palette.primary, 0.77)};
    border-color: ${({ theme }) => rgba(theme.palette.primary, 0.77)};
  }
`;

export const StyledActionBtn = styled.div`
  display: flex;
  cursor: pointer;
`;

export const StyledBlock = styled.div`
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 16px;
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto;
  background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};

  &:hover ${StyledBlockActions} {
    opacity: 1;
  }
`;

export const StyledUploadInput = styled(Upload)`
  display: block;

  & .ant-upload {
    display: block;
  }
`;

export const StyledUploadButton = styled(Button)`
  text-align: left;
`;

export const StyledCheckbox = styled(Checkbox)`
  & .ant-checkbox-inner {
    border-radius: 4px;
    width: 18px;
    height: 18px;

    &::after {
      width: 6px;
      height: 11px;
      top: 46%;
    }
  }
`;
