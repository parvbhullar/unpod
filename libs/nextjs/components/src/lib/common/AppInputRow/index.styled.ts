import styled from 'styled-components';
import {
  Button,
  Checkbox,
  DatePicker,
  Input,
  Select,
  TimePicker,
  Typography,
} from 'antd';
import { rgba } from 'polished';

const { Text } = Typography;

type StyledRootProps = {
  isOver?: boolean;};

export const StyledRoot = styled.div<StyledRootProps>`
  display: flex;
  align-items: center;
  gap: 12px;
  border-radius: 10px;
  padding: ${({ isOver }) => (isOver ? `0 5px` : 0)};
  background-color: ${({ isOver, theme }) =>
    isOver
      ? rgba(theme.palette.primary, 0.55)
      : theme.palette.background.default};
  transition: all 0.3s ease;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: ${({ isOver }) => (isOver ? `5px` : 0)};
  }

  & .ant-row {
    flex: 1;
  }
`;

export const StyledDragHandle = styled.div`
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: move;
  opacity: 0.5;
  transition: opacity 0.3s ease;

  &:hover {
    opacity: 1;
  }
`;

export const StyledContainer = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    flex-wrap: wrap;
  }
`;

export const StyledCheckbox = styled(Checkbox)`
  & .ant-checkbox-inner {
    height: 20px;
    width: 20px;
    border-radius: 6px;
    border-width: 2px;
    background-color: ${({ theme }) => theme.palette.common.white};

    &::after {
      height: 12px;
      width: 6px;
      top: 44%;
      border-color: ${({ theme }) => theme.palette.primary};
    }
  }

  &:hover .ant-checkbox-inner::after {
    border-color: ${({ theme }) => theme.palette.common.white};
  }
`;

export const StyledActions = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 5px;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    justify-content: flex-start;
  }
`;

export const StyledButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0 !important;
  height: auto !important;
  border-radius: 50%;
  padding: 3px;
  transition: all 0.3s ease;
`;

export const StyledInputWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  //height: 100%;
`;

export const StyledRowContainer = styled.div`
  min-width: calc(100% - 182px);
  width: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    flex-wrap: wrap;
  }
`;

export const StyledActionsWrapper = styled(StyledInputWrapper)`
  justify-content: flex-end;
  width: 170px;
  margin: 0 0 0 auto;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    width: 100%;
    justify-content: flex-start;
  }
`;

export const StyledLabel = styled(Text)`
  min-width: 96px;
  display: none;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    display: inline-block;
  }
`;

export const StyledInput = styled(Input)`
  flex: 1;

  & .ant-input-prefix,
  & .ant-input-surfix {
    margin-inline-end: 10px;
  }
`;
export const StyledSelect = styled(Select)`
  width: 100%;

  & .ant-input-prefix,
  & .ant-input-surfix {
    margin-inline-end: 10px;
  }
`;

export const StyledDatePicker = styled(DatePicker)`
  flex: 1;

  & .ant-input-prefix,
  & .ant-input-surfix {
    margin-inline-end: 10px;
  }
`;

export const StyledTimePicker = styled(TimePicker)`
  flex: 1;
`;
