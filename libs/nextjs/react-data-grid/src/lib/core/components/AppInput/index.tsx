import React, { ChangeEvent, useEffect, useState } from 'react';
import type { InputProps } from 'antd';
import { Input } from 'antd';
import clsx from 'clsx';
import AppFloatingOutline from '../AppFloatingOutline';

type Props = {
  placeholder: string;
  className?: string;
  style?: React.CSSProperties;
  defaultValue?: string;
  value?: string;
  disabled?: boolean;
  onChange?: (event: ChangeEvent<HTMLInputElement>) => void;
  asterisk?: boolean;
};

export const AppInput = ({
  placeholder,
  className,
  style,
  value,
  disabled,
  defaultValue,
  onChange,
  asterisk,
  ...restProps
}: InputProps & Props) => {
  const [inputVal, setInputVal] = useState<string>('');

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
      className={clsx('global-input', className)}
      style={style}
      disabled={disabled}
      value={inputVal}
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
      />
    </AppFloatingOutline>
  );
};

export default React.memo(AppInput);
