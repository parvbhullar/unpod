'use client';
import React, {
  CSSProperties,
  ReactNode,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import clsx from 'clsx';
import { Select } from 'antd';
import AppFloatingOutline from '../AppFloatingOutline';
import type { BaseSelectRef } from '@rc-component/select';
import type { SelectProps } from 'antd/es/select';

type AppSelectProps = {
  placeholder?: ReactNode;
  children?: ReactNode;
  defaultValue?: string | number | object | unknown[] | null;
  value?: string | number | object | unknown[] | null;
  className?: string;
  style?: CSSProperties;
  disabled?: boolean;
  onChange?: (value: string | number | object | unknown[] | null) => void;
  asterisk?: boolean;
  loading?: boolean;
  suffixIcon?: ReactNode;
  id?: string;
  [key: string]: unknown;};

const AppSelect: React.FC<AppSelectProps> = ({
  placeholder,
  children,
  defaultValue,
  value,
  className = '',
  style,
  disabled = false,
  onChange,
  asterisk,
  loading,
  suffixIcon,
  ...restProps
}) => {
  const [inputVal, setInputVal] = useState<
    string | number | object | unknown[] | null
  >(value ?? defaultValue ?? null);
  const inputRef = useRef<BaseSelectRef | null>(null);
  const inputId = useMemo(() => {
    if (restProps?.id) return String(restProps.id);
    return (
      inputRef.current?.nativeElement
        ?.querySelector('input')
        ?.getAttribute('id') || ''
    );
  }, [restProps?.id]);

  useEffect(() => {
    setInputVal(value ?? defaultValue ?? null);
  }, [value, defaultValue]);

  const onSelectChange: SelectProps['onChange'] = (val) => {
    setInputVal(val);
    if (onChange) onChange(val as string | number | object | unknown[] | null);
  };

  const placeholderText = typeof placeholder === 'string' ? placeholder : '';

  return (
    <AppFloatingOutline
      placeholder={placeholderText}
      className={clsx('app-select', className)}
      style={style}
      value={inputVal}
      disabled={disabled}
      eleID={inputId}
      asterisk={asterisk}
    >
      <Select
        placeholder=""
        maxTagCount="responsive"
        onChange={onSelectChange}
        defaultValue={defaultValue}
        value={inputVal}
        loading={loading}
        suffixIcon={loading ? undefined : suffixIcon}
        disabled={disabled}
        {...restProps}
        ref={inputRef}
      >
        {children}
      </Select>
    </AppFloatingOutline>
  );
};

export default AppSelect;
