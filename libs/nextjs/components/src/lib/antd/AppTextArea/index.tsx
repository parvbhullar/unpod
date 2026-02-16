'use client';
import React, {
  ChangeEvent,
  CSSProperties,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { Input } from 'antd';
import AppFloatingOutline from '../AppFloatingOutline';
import type { TextAreaRef } from 'antd/es/input/TextArea';

type AppTextAreaProps = {
  placeholder: string;
  className?: string;
  style?: CSSProperties;
  onChange?: (event: ChangeEvent<HTMLTextAreaElement>) => void;
  defaultValue?: string;
  value?: string;
  disabled?: boolean;
  asterisk?: boolean;
  id?: string;
  [key: string]: unknown;};

const AppTextArea: React.FC<AppTextAreaProps> = ({
  placeholder,
  className = '',
  style,
  onChange,
  defaultValue,
  value,
  disabled = false,
  asterisk,
  ...restProps
}) => {
  const [inputVal, setInputVal] = useState<string>('');
  const inputRef = useRef<TextAreaRef | null>(null);
  const inputId = useMemo(() => {
    if (restProps?.id) return String(restProps.id);
    return (
      inputRef.current?.resizableTextArea?.textArea?.getAttribute('id') || ''
    );
  }, [restProps?.id]);

  useEffect(() => {
    setInputVal(value || defaultValue || '');
  }, [value, defaultValue]);

  const onInputChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setInputVal(event.target.value);
    if (onChange) onChange(event);
  };

  return (
    <AppFloatingOutline
      placeholder={placeholder}
      className={`app-textarea ${className}`}
      style={style}
      value={inputVal}
      disabled={disabled}
      eleID={inputId}
      asterisk={asterisk}
    >
      <Input.TextArea
        placeholder=""
        autoComplete="off"
        value={inputVal}
        disabled={disabled}
        defaultValue={defaultValue}
        onChange={onInputChange}
        {...restProps}
        ref={inputRef}
      />
    </AppFloatingOutline>
  );
};

export default React.memo(AppTextArea);
