import React from 'react';
import styled from 'styled-components';
import { Input, type InputRef } from 'antd';

import type { RenderEditCellProps } from '../models/data-grid';

const StyledInput = styled(Input)`
  border-width: 2px;
  vertical-align: top;

  &.ant-input {
    border-radius: 2px;
    height: 100%;
    width: 100%;
  }
`;

export default function textEditor<TRow, TSummaryRow>({
  row,
  column,
  onRowChange,
  onClose,
}: RenderEditCellProps<TRow, TSummaryRow>) {
  const editorRef = React.useRef<InputRef>(null);

  React.useEffect(() => {
    editorRef.current?.focus();
    // editorRef.current?.select();
  }, []);

  return (
    <StyledInput
      size="small"
      ref={editorRef}
      value={row[column.dataIndex as keyof TRow] as unknown as string}
      onChange={(event) =>
        onRowChange({ ...row, [column.dataIndex]: event.target.value })
      }
      onBlur={() => onClose(true, false)}
    />
  );
}
