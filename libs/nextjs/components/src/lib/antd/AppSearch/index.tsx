'use client';
import React, {ChangeEvent, CSSProperties, useEffect, useRef, useState,} from 'react';
import {Input} from 'antd';
import AppFloatingOutline from '../AppFloatingOutline';
import {InputRef} from 'antd/es/input';

type AppSearchProps = {
  placeholder: string;
  className?: string;
  style?: CSSProperties;
  onChange?: (event: ChangeEvent<HTMLInputElement>) => void;
  defaultValue?: string;
  disabled?: boolean;
  value?: string;
  asterisk?: boolean;
  [key: string]: unknown;
};

const AppSearch: React.FC<AppSearchProps> = ({
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
      className={`app-search ${className}`}
      style={style}
      disabled={disabled}
      value={inputVal}
      eleID={(inputRef?.current as { input?: { id?: string } })?.input?.id}
      asterisk={asterisk}
    >
      <Input.Search
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

export default React.memo(AppSearch);
