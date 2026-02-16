'use client';
import React, {
  ChangeEvent,
  CSSProperties,
  ReactNode,
  useEffect,
  useRef,
  useState,
} from 'react';
import AppFloatingOutline from '../AppFloatingOutline';
import { Input } from 'antd';
import clsx from 'clsx';
import { InputRef } from 'antd/es/input';

type AppInputProps = {
  placeholder: string;
  className?: string;
  style?: CSSProperties;
  value?: string | number;
  disabled?: boolean | undefined;
  defaultValue?: string | number;
  onChange?: (event: ChangeEvent<HTMLInputElement>) => void;
  asterisk?: boolean;
  addonBefore?: boolean | ReactNode;
  id?: string;
  [key: string]: unknown;};

const AppInput: React.FC<AppInputProps> = ({
  placeholder,
  className = '',
  style,
  value,
  disabled = false,
  defaultValue,
  onChange,
  asterisk,
  ...restProps
}) => {
  const [inputVal, setInputVal] = useState<string | number | undefined>('');
  const inputRef = useRef<InputRef>(null);
  const inputId = restProps?.id || inputRef?.current?.input?.id || '';

  useEffect(() => {
    setInputVal(value || defaultValue);
  }, [value, defaultValue]);

  const onInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    setInputVal(event.target.value);
    if (onChange) onChange(event);
  };

  return (
    <AppFloatingOutline
      placeholder={placeholder}
      addonBefore={restProps?.addonBefore}
      className={clsx('app-input', className)}
      style={style}
      disabled={disabled}
      value={inputVal}
      eleID={inputId}
      asterisk={asterisk}
    >
      <Input
        autoComplete="off"
        placeholder=""
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

export default AppInput;
