import styled from 'styled-components';
import { DatePicker, Input, InputNumber, Popover, Select } from 'antd';
import { rgba } from 'polished';

export const StyledRoot = styled.div`
  width: 260px;
`;

export const StyledPopover = styled(Popover)`
  // margin-block: 10px;

  & .ant-popover-inner {
    padding: 12px 0;
    border: 3px solid red;
  }
`;

export const StyledTitleContainer = styled.div`
  padding: 12px 12px 0;
  border-block-end: 1px solid
    ${({ theme }: { theme: any }) =>
      rgba(theme.primaryColor ?? theme.palette?.primary ?? '#6c47ff', 0.11)};

  & .ant-popover-title {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
`;

export const StyledMoreHandle = styled.span`
  cursor: pointer;
  font-size: 16px;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  // padding: 0 4px 3px;

  &.active {
  }
`;

export const StyledFlexRow = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding-inline: 13px;
  margin-bottom: 12px;
`;

export const StyledFilterContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-inline: 13px;
`;

export const StyledInput = styled(Input)`
  height: 36px;
  border-radius: ${({ theme }) => theme.radius.sm}px !important;
`;

export const StyledSelect = styled(Select)`
  width: 100%;
  height: 36px;

  & .ant-select-selector {
    border-radius: ${({ theme }) => theme.radius.sm}px !important;
  }
`;

export const StyledInputNumber = styled(InputNumber)`
  width: 100%;
  height: 36px;
  line-height: 2.4;
  border-radius: ${({ theme }) => theme.radius.sm}px;

  & .ant-input-number-handler-wrap {
    border-start-end-radius: ${({ theme }) => theme.radius.sm}px;
    border-end-end-radius: ${({ theme }) => theme.radius.sm}px;
  }
`;
export const StyledDatePicker = styled(DatePicker)`
  width: 100%;
  height: 36px;
  border-radius: ${({ theme }) => theme.radius.sm}px;

  & .ant-input-number-handler-wrap {
    border-start-end-radius: ${({ theme }) => theme.radius.sm}px;
    border-end-end-radius: ${({ theme }) => theme.radius.sm}px;
  }
`;

export const StyledRangePicker = styled(DatePicker.RangePicker)`
  width: 100%;
  height: 36px;
  border-radius: ${({ theme }) => theme.radius.sm}px;

  & .ant-input-number-handler-wrap {
    border-start-end-radius: ${({ theme }) => theme.radius.sm}px;
    border-end-end-radius: ${({ theme }) => theme.radius.sm}px;
  }
`;

export const StyledActions = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 12px;
  border-block-start: 1px solid
    ${({ theme }: { theme: any }) =>
      rgba(theme.primaryColor ?? theme.palette?.primary ?? '#6c47ff', 0.11)};
  margin-block-start: 12px;
`;
