import styled from 'styled-components';
import { InputNumber } from 'antd';

import type { RenderEditCellProps } from '../models/data-grid';

const StyledInput = styled(InputNumber)`
  border-width: 2px;
  vertical-align: top;

  &.ant-input-number {
    border-radius: 2px;
    height: 100%;
    width: 100%;

    & .ant-input-number-input-wrap,
    & .ant-input-number-input {
      height: 100%;
    }
  }
`;

function autoFocusAndSelect(input: HTMLInputElement | null) {
  input?.focus();
  // input?.select();
}

export default function numberEditor<TRow, TSummaryRow>({
  row,
  column,
  onRowChange,
  onClose,
}: RenderEditCellProps<TRow, TSummaryRow>) {
  return (
    <StyledInput
      size="small"
      ref={autoFocusAndSelect}
      value={row[column.dataIndex as keyof TRow] as unknown as number}
      onChange={(newValue) =>
        onRowChange({ ...row, [column.dataIndex]: newValue })
      }
      onBlur={() => onClose(true, false)}
    />
  );
}
