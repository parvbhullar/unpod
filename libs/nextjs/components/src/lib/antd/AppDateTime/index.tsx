'use client';
import React, {
  CSSProperties,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import AppFloatingOutline from '../AppFloatingOutline';
import { DatePicker } from 'antd';
import { Dayjs } from 'dayjs';
import type { PickerRef } from '@rc-component/picker/es/interface';

type AppDateTimeProps = {
  placeholder: string;
  className?: string;
  style?: CSSProperties;
  defaultValue?: Dayjs | null;
  value?: Dayjs | null;
  disabled?: boolean;
  onChange?: (date: Dayjs | null, dateString: string | string[] | null) => void;
  asterisk?: boolean;
  id?: string;
  [key: string]: unknown;};

const AppDateTime: React.FC<AppDateTimeProps> = ({
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
  const [inputVal, setInputVal] = useState<Dayjs | null | undefined>(
    defaultValue || value || null,
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
    setInputVal(date);
    if (onChange) onChange(date, dateString);
  };

  return (
    <AppFloatingOutline
      placeholder={placeholder}
      className={`app-datetime ${className}`}
      style={style}
      disabled={disabled}
      value={inputVal}
      eleID={inputId}
      asterisk={asterisk}
    >
      <DatePicker
        placeholder=""
        showTime={{ format: 'HH:mm' }}
        format="DD-MM-YYYY HH:mm"
        value={inputVal}
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

export default React.memo(AppDateTime);
