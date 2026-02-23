import React from 'react';
import MDEditor, {type MDEditorProps} from '@uiw/react-md-editor';
import {StyledContainer} from './index.styled';

type AppMarkdownEditorProps = {
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  bordered?: boolean;
  rows?: number;
} & Omit<MDEditorProps, 'value' | 'onChange' | 'textareaProps'>;

const AppMarkdownEditor: React.FC<AppMarkdownEditorProps> = ({
                                                               value = '',
                                                               onChange,
                                                               placeholder = 'Write here...',
                                                               bordered = false,
                                                               rows = 8,
                                                               ...props
                                                             }) => {
  const editorHeight = Math.max(rows * 24, 192);

  return (
    <StyledContainer bordered={bordered} data-color-mode="light">
      <MDEditor
        value={value}
        onChange={(nextValue) => onChange?.(nextValue ?? '')}
        preview="edit"
        height={editorHeight}
        visibleDragbar={false}
        textareaProps={{
          placeholder,
          rows,
        }}
        {...props}
      />
    </StyledContainer>
  );
};

export default AppMarkdownEditor;
