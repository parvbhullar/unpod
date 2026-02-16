'use client';
import React, { CSSProperties, useEffect, useRef, useState } from 'react';
import AppFloatingOutline from '../AppFloatingOutline';
import { InputNumber } from 'antd';

type AppInputNumberProps = {
  placeholder: string;
  className?: string;
  style?: CSSProperties;
  defaultValue?: number;
  disabled?: boolean;
  value?: number;
  onChange?: (value: number | null) => void;
  setFocus?: boolean;
  asterisk?: boolean;
  [key: string]: unknown;};

const AppInputNumber: React.FC<AppInputNumberProps> = ({
  placeholder,
  className = '',
  style,
  defaultValue,
  disabled = false,
  value,
  onChange,
  setFocus,
  asterisk,
  ...restProps
}) => {
  const [inputVal, setInputVal] = useState<number | string | undefined>(
    value || defaultValue || '',
  );

  const inputRef = useRef<React.ComponentRef<typeof InputNumber> | null>(null);

  useEffect(() => {
    if (setFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [setFocus]);

  useEffect(() => {
    setInputVal(value || defaultValue);
  }, [value, defaultValue]);

  const onInputChange = (val: number | null) => {
    setInputVal(val ?? '');
    if (onChange) onChange(val);
  };

  return (
    <AppFloatingOutline
      placeholder={placeholder}
      className={`app-input-number ${className}`}
      style={style}
      value={inputVal}
      disabled={disabled}
      eleID={
        (inputRef?.current as unknown as { props?: { id?: string } })?.props?.id
      }
      asterisk={asterisk}
    >
      <InputNumber
        placeholder=""
        autoComplete="off"
        onChange={onInputChange}
        defaultValue={defaultValue}
        value={inputVal as number}
        disabled={disabled}
        {...restProps}
        style={style}
        ref={inputRef}
      />
    </AppFloatingOutline>
  );
};

export default React.memo(AppInputNumber);
