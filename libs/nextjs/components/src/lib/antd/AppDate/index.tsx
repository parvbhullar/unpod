'use client';
import React, {CSSProperties, useEffect, useMemo, useRef, useState,} from 'react';
import AppFloatingOutline from '../AppFloatingOutline';
import {DatePicker} from 'antd';
import {Dayjs} from 'dayjs';
import type {PickerRef} from '@rc-component/picker/es/interface';

type AppDateProps = {
  placeholder: string;
  className?: string;
  style?: CSSProperties;
  defaultValue?: Dayjs | null;
  value?: Dayjs | null;
  disabled?: boolean;
  onChange?: (date: Dayjs | null, dateString: string | string[] | null) => void;
  asterisk?: boolean;
  id?: string;
  [key: string]: unknown;
};

const AppDate: React.FC<AppDateProps> = ({
                                           placeholder,
                                           className = '',
                                           style,
                                           defaultValue,
                                           value,
                                           disabled = false,
                                           onChange,
                                           asterisk,
                                           ...restProps
                                         }) => {
  const [inputVal, setInputVal] = useState<string | Dayjs | null | undefined>(
    defaultValue || value || '',
  );
  const inputRef = useRef<PickerRef | null>(null);
  const inputId = useMemo(() => {
    if (restProps?.id) return String(restProps.id);
    return (
      inputRef.current?.nativeElement
        ?.querySelector('input')
        ?.getAttribute('id') || ''
    );
  }, [restProps?.id]);

  useEffect(() => {
    setInputVal(value || defaultValue);
  }, [value, defaultValue]);

  const onDatePickerChange = (
    date: Dayjs | null,
    dateString: string | string[] | null,
  ) => {
    setInputVal(dateString as string);
    if (onChange) onChange(date, dateString);
  };

  return (
    <AppFloatingOutline
      placeholder={placeholder}
      className={`app-date ${className}`}
      style={style}
      value={inputVal}
      disabled={disabled}
      eleID={inputId}
      asterisk={asterisk}
    >
      <DatePicker
        placeholder=""
        format="DD-MM-YYYY"
        value={value}
        autoComplete="off"
        disabled={disabled}
        defaultValue={defaultValue}
        onChange={onDatePickerChange}
        {...restProps}
        ref={inputRef}
      />
    </AppFloatingOutline>
  );
};

export default AppDate;
