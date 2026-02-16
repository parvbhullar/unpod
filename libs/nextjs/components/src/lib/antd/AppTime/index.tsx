'use client';
import React, {
  CSSProperties,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import AppFloatingOutline from '../AppFloatingOutline';
import { TimePicker } from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import type { PickerRef } from '@rc-component/picker/es/interface';

type AppTimeProps = {
  placeholder: string;
  className?: string;
  style?: CSSProperties;
  defaultValue?: Dayjs | null;
  value?: Dayjs | null;
  onChange?: (date: Dayjs | null, dateString: string | string[] | null) => void;
  disabled?: boolean;
  asterisk?: boolean;
  id?: string;
  [key: string]: unknown;};

const AppTime: React.FC<AppTimeProps> = ({
  placeholder,
  className = '',
  style,
  defaultValue,
  value,
  onChange,
  disabled = false,
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
      className={`app-time ${className}`}
      style={style}
      value={inputVal}
      disabled={disabled}
      eleID={inputId}
      asterisk={asterisk}
    >
      <TimePicker
        placeholder=""
        value={inputVal}
        autoComplete="off"
        disabled={disabled}
        defaultValue={defaultValue}
        defaultOpenValue={dayjs('00:00:00', 'HH:mm:ss')}
        onChange={onDatePickerChange}
        {...restProps}
        ref={inputRef}
      />
    </AppFloatingOutline>
  );
};

export default AppTime;
