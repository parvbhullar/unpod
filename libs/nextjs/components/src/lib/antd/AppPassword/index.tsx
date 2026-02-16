'use client';
import React, {
  ChangeEvent,
  CSSProperties,
  useEffect,
  useRef,
  useState,
} from 'react';
import AppFloatingOutline from '../AppFloatingOutline';
import type { InputRef } from 'antd';
import { Input } from 'antd';

type AppPasswordProps = {
  placeholder: string;
  className?: string;
  style?: CSSProperties;
  onChange?: (event: ChangeEvent<HTMLInputElement>) => void;
  defaultValue?: string;
  disabled?: boolean;
  value?: string;
  asterisk?: boolean;
  [key: string]: unknown;};

const AppPassword: React.FC<AppPasswordProps> = ({
  placeholder,
  className = '',
  style,
  onChange,
  defaultValue,
  disabled = false,
  value,
  asterisk,
  ...restProps
}) => {
  const [inputVal, setInputVal] = useState<string>('');
  const inputRef = useRef<InputRef>(null);

  useEffect(() => {
    setInputVal(value || defaultValue || '');
  }, [value, defaultValue]);

  const onInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    setInputVal(event.target.value);
    if (onChange) onChange(event);
  };

  return (
    <AppFloatingOutline
      placeholder={placeholder}
      className={`app-password ${className}`}
      style={style}
      value={inputVal}
      disabled={disabled}
      eleID={
        (inputRef?.current as { props?: { id?: string | undefined } })?.props
          ?.id
      }
      asterisk={asterisk}
    >
      <Input.Password
        placeholder=""
        autoComplete="off"
        value={inputVal}
        disabled={disabled}
        defaultValue={defaultValue}
        onChange={onInputChange}
        role="password-textbox"
        {...restProps}
        ref={inputRef}
      />
    </AppFloatingOutline>
  );
};

export default React.memo(AppPassword);
