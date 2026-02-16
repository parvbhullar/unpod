import type { DatePickerProps } from 'antd';
import { DatePicker, TimePicker } from 'antd';
import styled from 'styled-components';
import type { RenderEditCellProps } from '../models/data-grid';
import { getDateObject } from '../helpers/DateHelper';

const StyledDatePicker = styled(DatePicker)`
  border-width: 2px;
  vertical-align: top;

  &.ant-picker {
    height: 100%;
    border-radius: 2px;
  }
`;
const StyledTimePicker = styled(TimePicker)`
  border-width: 2px;
  vertical-align: top;

  &.ant-picker {
    height: 100%;
    border-radius: 2px;
  }
`;

const DateInput = <TRow, TSummaryRow>({
  row,
  column,
  onRowChange,
  onClose,
}: RenderEditCellProps<TRow, TSummaryRow>) => {
  return (
    <StyledDatePicker
      size="small"
      value={
        row[column.dataIndex as keyof TRow]
          ? getDateObject(
              String(
                row[column.dataIndex as keyof TRow] as DatePickerProps['value'],
              ),
            )
          : null
      }
      onChange={(date, dateString) =>
        onRowChange({ ...row, [column.dataIndex]: dateString })
      }
      onBlur={() => onClose(true, false)}
    />
  );
};

export const DateTimeInput = <TRow, TSummaryRow>({
  row,
  column,
  onRowChange,
  onClose,
}: RenderEditCellProps<TRow, TSummaryRow>) => {
  return (
    <StyledDatePicker
      size="small"
      value={
        row[column.dataIndex as keyof TRow]
          ? getDateObject(
              String(
                row[column.dataIndex as keyof TRow] as DatePickerProps['value'],
              ),
            )
          : null
      }
      onChange={(date, dateString) =>
        onRowChange({ ...row, [column.dataIndex]: dateString })
      }
      onBlur={() => onClose(true, false)}
      showTime
    />
  );
};

export const TimeInput = <TRow, TSummaryRow>({
  row,
  column,
  onRowChange,
  onClose,
}: RenderEditCellProps<TRow, TSummaryRow>) => {
  return (
    <StyledTimePicker
      size="small"
      value={
        row[column.dataIndex as keyof TRow]
          ? getDateObject(
              String(
                row[column.dataIndex as keyof TRow] as DatePickerProps['value'],
              ),
              'HH:mm:ss',
            )
          : null
      }
      onChange={(date, dateString) =>
        onRowChange({ ...row, [column.dataIndex]: dateString })
      }
      onBlur={() => onClose(true, false)}
    />
  );
};

export default DateInput;
