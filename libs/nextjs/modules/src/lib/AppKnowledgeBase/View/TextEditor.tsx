import {useEffect, useRef} from 'react';
import {Input, type InputRef} from 'antd';
import styled from 'styled-components';

const StyledInput = styled(Input)`
  border-width: 2px;
  vertical-align: top;

  &.ant-input {
    border-radius: 2px;
    height: 100%;
    width: 100%;
  }
`;

type TextEditorProps = {
  row: Record<string, any>;
  column: { dataIndex: string };
  onRowChange: (row: Record<string, any>) => void;
  onClose: (commit: boolean, cancel: boolean) => void;
};

const TextEditor = ({row, column, onRowChange, onClose}: TextEditorProps) => {
  const editorRef = useRef<InputRef | null>(null);

  useEffect(() => {
    editorRef.current?.focus();
    // editorRef.current?.select();
  }, []);

  return (
    <StyledInput
      size="small"
      ref={editorRef}
      value={row[column.dataIndex]}
      onChange={(event) =>
        onRowChange({...row, [column.dataIndex]: event.target.value})
      }
      onBlur={() => onClose(true, false)}
    />
  );
};

export default TextEditor;
