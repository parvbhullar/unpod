import React, {useRef, useState} from 'react';
import {StyledEditor, StyledPlaceholder} from './index.styled';
import {EditorProps} from '@monaco-editor/react';
import {editor} from 'monaco-editor';

type AppCodeEditorProps = EditorProps & {
  placeholder?: string;
};

const AppCodeEditor: React.FC<AppCodeEditorProps> = ({
                                                       placeholder = 'Write Python code here...',
                                                       defaultLanguage = 'python',
                                                       ...props
                                                     }) => {
  const [value, setValue] = useState('');
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  function handleEditorDidMount(editor: editor.IStandaloneCodeEditor) {
    editorRef.current = editor;
    setValue(editor.getValue());
  }

  return (
    <div style={{position: 'relative'}}>
      <StyledEditor
        height="30vh"
        onMount={handleEditorDidMount}
        options={{
          minimap: {enabled: false},
          wordWrap: 'on',
          lineNumbersMinChars: 3,
        }}
        defaultLanguage={defaultLanguage}
        {...props}
      />
      <StyledPlaceholder
        hidden={!!(editorRef.current?.getValue() || value)}
        type="secondary"
      >
        {placeholder}
      </StyledPlaceholder>
    </div>
  );
};

export default AppCodeEditor;
