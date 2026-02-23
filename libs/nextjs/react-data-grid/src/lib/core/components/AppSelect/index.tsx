import React, {useEffect, useState} from 'react';
import clsx from 'clsx';
import type {SelectProps} from 'antd';
import {Select} from 'antd';
import AppFloatingOutline from '../AppFloatingOutline';

type Props = {
  placeholder: string;
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  defaultValue?: string | string[];
  value?: string | string[];
  onChange?: SelectProps['onChange'];
  disabled?: boolean;
  asterisk?: boolean;
  [key: string]: any;
};

export const AppSelect = ({
                            placeholder,
                            children,
                            defaultValue,
                            value,
                            className,
                            style,
                            disabled,
                            onChange,
                            asterisk,
                            ...restProps
                          }: SelectProps & Props) => {
  const [inputVal, setInputVal] = useState<string>();

  useEffect(() => {
    setInputVal(value || defaultValue || undefined);
  }, [value, defaultValue]);

  const onSelectChange: SelectProps['onChange'] = (value, option) => {
    setInputVal(value);
    if (onChange) onChange(value, option);
  };

  return (
    <AppFloatingOutline
      placeholder={placeholder}
      className={clsx('global-select', className)}
      style={style}
      value={inputVal}
      disabled={disabled}
      asterisk={asterisk}
    >
      <Select
        placeholder=""
        maxTagCount="responsive"
        onChange={onSelectChange}
        defaultValue={defaultValue}
        value={inputVal}
        disabled={disabled}
        {...restProps}
      >
        {children}
      </Select>
    </AppFloatingOutline>
  );
};

export default React.memo(AppSelect);
